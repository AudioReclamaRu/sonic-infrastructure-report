"""Durable safeguards for the Telegram editorial publishing pipeline.

The Telegram Bot API has no idempotency key for sendMessage/sendPhoto.  This
module therefore uses an at-most-once send attempt: it durably records SENDING
before the HTTP request and parks ambiguous outcomes as UNKNOWN.  Operators
must reconcile UNKNOWN records instead of letting the scheduler resend them.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ACTIVE_STATUSES = ("SENDING", "SENT", "UNKNOWN")
TRACKING_KEYS = {
    "fbclid", "gclid", "dclid", "msclkid", "yclid", "mc_cid", "mc_eid",
}
ACRONYM_RE = re.compile(r"(?<![A-Za-z])[A-Z][A-Z0-9]{1,9}(?![A-Za-z])")
# Known harmful phonetic renderings. New source-specific forms belong in the
# concept's abbreviations.<TOKEN>.forbidden_transliterations list.
KNOWN_BAD_TRANSLITERATIONS = {
    "GOP": ("гоппартия", "гоп партия", "гоп-партия"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonicalize_url(url: str) -> str:
    """Normalize a source URL for identity checks, not for display."""
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return ""
        host = parsed.hostname.lower()
        if host.startswith("www."):
            host = host[4:]
        port = parsed.port
        netloc = host
        if port and not ((parsed.scheme.lower() == "http" and port == 80)
                         or (parsed.scheme.lower() == "https" and port == 443)):
            netloc += ":" + str(port)
        path = re.sub(r"/{2,}", "/", parsed.path or "/")
        if path != "/":
            path = path.rstrip("/")
        kept = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            key_low = key.lower()
            if key_low.startswith("utm_") or key_low in TRACKING_KEYS:
                continue
            kept.append((key, value))
        query = urlencode(sorted(kept))
        return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))
    except (TypeError, ValueError):
        return ""


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold().replace("ё", "е")
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^0-9a-zа-я]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def content_fingerprint(value: str) -> str:
    normalized = normalize_text(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def similarity_score(left: str, right: str) -> float:
    a = normalize_text(left)
    b = normalize_text(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    seq = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    ta, tb = set(a.split()), set(b.split())
    union = ta | tb
    jaccard = len(ta & tb) / len(union) if union else 0.0
    return max(seq, jaccard)


def event_key_for_item(item: dict, concept: dict | None = None) -> str:
    """Prefer an explicit event key; otherwise derive a conservative stable key."""
    concept = concept or {}
    explicit = (item.get("event_key") or concept.get("event_key") or "").strip()
    if explicit:
        slug = re.sub(r"[^a-zA-Z0-9._:-]+", "-", explicit).strip("-").lower()
        if slug:
            return "event:" + slug
    source = canonicalize_url(item.get("src", ""))
    if source:
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:40]
        return "source:" + digest
    payload = " ".join((item.get("title", ""), item.get("desc", "")))
    return "content:" + content_fingerprint(payload)[:40]


def abbreviation_issues(text: str, concept: dict) -> list[str]:
    """Check editorial-v2 foreign acronyms and reject phonetic Cyrillic aliases.

    Each acronym used in the visible copy must be either expanded before its
    first occurrence or explicitly preserved in its original Latin spelling.
    The policy is opt-in by editorial_version=2 so legacy posts remain readable.
    """
    if int(concept.get("editorial_version") or 1) < 2:
        return []
    policy = concept.get("abbreviations")
    if not isinstance(policy, dict):
        return ["abbreviation_policy_missing"]

    issues: list[str] = []
    found = {m.group(0) for m in ACRONYM_RE.finditer(text)}
    unknown = sorted(found - set(policy))
    if unknown:
        issues.append("abbreviations_unreviewed:" + ",".join(unknown))

    for token in sorted(found & set(policy)):
        entry = policy.get(token) or {}
        if not isinstance(entry, dict):
            issues.append("abbreviation_policy_invalid:" + token)
            continue
        mode = entry.get("mode")
        first_pos = text.find(token)
        if mode == "expanded":
            expansion = (entry.get("expansion") or "").strip()
            if not expansion or expansion not in text[:first_pos]:
                issues.append("abbreviation_not_expanded_before_first_use:" + token)
        elif mode == "original":
            if not re.search(r"(?<![A-Za-z])" + re.escape(token) +
                             r"(?![A-Za-z])", text):
                issues.append("abbreviation_not_preserved_original:" + token)
        else:
            issues.append("abbreviation_mode_invalid:" + token)

        forbidden = list(entry.get("forbidden_transliterations") or [])
        forbidden.extend(KNOWN_BAD_TRANSLITERATIONS.get(token, ()))
        lowered = text.casefold()
        for bad in forbidden:
            bad = str(bad).strip().casefold()
            if bad and bad in lowered:
                issues.append("abbreviation_phonetic_transliteration:" + token)
                break

    # A known Cyrillic phonetic rendering is rejected even if the acronym was
    # omitted from the visible text or the item was not supplied with a policy.
    lowered = text.casefold()
    for token, forms in KNOWN_BAD_TRANSLITERATIONS.items():
        for bad in forms:
            if bad in lowered:
                issues.append("known_bad_transliteration:" + token)
                break
    return sorted(set(issues))


class PublicationLedger:
    """SQLite event ledger enforcing duplicate blocking and conservative retries."""

    def __init__(self, path: str | Path, near_duplicate_threshold: float = 0.86):
        self.path = str(path)
        self.near_duplicate_threshold = near_duplicate_threshold
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=15000")
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS publications (
                    event_key TEXT PRIMARY KEY,
                    guid TEXT NOT NULL,
                    canonical_url TEXT NOT NULL DEFAULT '',
                    fingerprint TEXT NOT NULL,
                    normalized_content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message_id TEXT NOT NULL DEFAULT '',
                    chat_id TEXT NOT NULL DEFAULT '',
                    media_kind TEXT NOT NULL DEFAULT '',
                    attempts INTEGER NOT NULL DEFAULT 1,
                    last_error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_publications_url_status "
                "ON publications(canonical_url, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_publications_fingerprint_status "
                "ON publications(fingerprint, status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_publications_guid "
                "ON publications(guid, status)"
            )

    @staticmethod
    def _active_clause() -> str:
        return "status IN ('SENDING', 'SENT', 'UNKNOWN')"

    @staticmethod
    def _result(decision: str, reason: str = "", row=None, score: float = 0.0):
        return {
            "decision": decision,
            "reason": reason,
            "event_key": row["event_key"] if row else "",
            "status": row["status"] if row else "",
            "message_id": row["message_id"] if row else "",
            "similarity": round(score, 4),
        }

    def reserve(
        self,
        event_key: str,
        guid: str,
        canonical_url: str,
        fingerprint: str,
        content: str,
    ) -> dict:
        """Durably reserve a send before any network request.

        Returns RESERVED, DUPLICATE, or REVIEW_REQUIRED. UNKNOWN and SENDING
        never auto-retry: the Telegram API may have accepted a request even if
        the client did not receive its response.
        """
        now = utc_now()
        normalized = normalize_text(content)
        canonical = canonicalize_url(canonical_url)
        fp = fingerprint or content_fingerprint(content)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT * FROM publications WHERE event_key=?", (event_key,)
            ).fetchone()
            if existing and existing["status"] != "FAILED":
                conn.commit()
                return self._result("DUPLICATE", "event_key_already_reserved", existing)

            if canonical:
                existing = conn.execute(
                    "SELECT * FROM publications WHERE canonical_url=? AND "
                    + self._active_clause() + " ORDER BY updated_at DESC LIMIT 1",
                    (canonical,),
                ).fetchone()
                if existing:
                    conn.commit()
                    return self._result("DUPLICATE", "canonical_source_already_used", existing)

            existing = conn.execute(
                "SELECT * FROM publications WHERE fingerprint=? AND "
                + self._active_clause() + " ORDER BY updated_at DESC LIMIT 1",
                (fp,),
            ).fetchone()
            if existing:
                conn.commit()
                return self._result("DUPLICATE", "content_fingerprint_already_used", existing)

            # Conservative semantic guard: near-matches are parked for editorial
            # review rather than silently published or automatically discarded.
            rows = conn.execute(
                "SELECT * FROM publications WHERE " + self._active_clause() +
                " ORDER BY updated_at DESC LIMIT 500"
            ).fetchall()
            for row in rows:
                score = similarity_score(normalized, row["normalized_content"])
                if score >= self.near_duplicate_threshold:
                    conn.commit()
                    return self._result(
                        "REVIEW_REQUIRED", "near_duplicate_requires_human_review",
                        row, score
                    )

            if existing is not None:
                pass
            if existing and existing["status"] == "FAILED":
                conn.execute(
                    "UPDATE publications SET guid=?, canonical_url=?, fingerprint=?, "
                    "normalized_content=?, status='SENDING', attempts=attempts+1, "
                    "last_error='', updated_at=? WHERE event_key=?",
                    (guid, canonical, fp, normalized, now, event_key),
                )
            else:
                conn.execute(
                    "INSERT INTO publications(event_key,guid,canonical_url,fingerprint,"
                    "normalized_content,status,attempts,created_at,updated_at) "
                    "VALUES(?,?,?,?,?,'SENDING',1,?,?)",
                    (event_key, guid, canonical, fp, normalized, now, now),
                )
            conn.commit()
        return {"decision": "RESERVED", "reason": "durable_send_intent", "event_key": event_key}

    def mark_sent(
        self, event_key: str, message_id: str, chat_id: str, media_kind: str = ""
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE publications SET status='SENT', message_id=?, chat_id=?, "
                "media_kind=?, last_error='', updated_at=? WHERE event_key=?",
                (str(message_id), str(chat_id), media_kind, utc_now(), event_key),
            )

    def mark_failed(self, event_key: str, error: str) -> None:
        """Only use when Telegram returned a definitive ok=false API response."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE publications SET status='FAILED', last_error=?, updated_at=? "
                "WHERE event_key=?",
                (str(error)[:2000], utc_now(), event_key),
            )

    def mark_unknown(self, event_key: str, error: str) -> None:
        """Park network timeouts/empty responses; never blindly send again."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE publications SET status='UNKNOWN', last_error=?, updated_at=? "
                "WHERE event_key=?",
                (str(error)[:2000], utc_now(), event_key),
            )

    def import_legacy_sent(
        self, event_key: str, guid: str, canonical_url: str, fingerprint: str,
        content: str, message_id: str = "", chat_id: str = "",
    ) -> None:
        """Hydrate the ledger from the historic guid tracker on first startup."""
        now = utc_now()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO publications(event_key,guid,canonical_url,"
                "fingerprint,normalized_content,status,message_id,chat_id,attempts,"
                "created_at,updated_at) VALUES(?,?,?,?,?,'SENT',?,?,1,?,?)",
                (event_key, guid, canonicalize_url(canonical_url), fingerprint,
                 normalize_text(content), str(message_id), str(chat_id), now, now),
            )

    def has_guid(self, guid: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM publications WHERE guid=? AND status='SENT' LIMIT 1",
                (guid,),
            ).fetchone()
        return row is not None

    def get_by_guid(self, guid: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM publications WHERE guid=? ORDER BY updated_at DESC LIMIT 1",
                (guid,),
            ).fetchone()
        return dict(row) if row else None

    def get_by_event_key(self, event_key: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM publications WHERE event_key=?", (event_key,)
            ).fetchone()
        return dict(row) if row else None
