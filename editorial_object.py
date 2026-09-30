# -*- coding: utf-8 -*-
"""
editorial_object.py — Editorial Object System for CULTURE OF VOICE.

Контракт: standards/editorial-object-contract.md
Принцип: НЕ генерировать cover независимо от editorial meaning.
Цель:   EVENT OBJECT -> ARTICLE + COVER, оба - представления одного изменения.

Модуль самодостаточен (only stdlib). Детерминированные правила, без LLM-суда
(прецедент: publication_gate проекта Первоисточник, mode=base).

Структура EVENT_OBJECT:
    {
      "subject":      "...",   # что движется в событии
      "action":       "...",   # что именно оно делает
      "before":       "...",   # как было раньше
      "after":        "...",   # как стало сейчас (ОБЯЗАТЕЛЬНО)
      "mechanism":    "...",   # за счёт чего произошло изменение (ОБЯЗАТЕЛЬНО)
      "consequence":  "...",   # что меняется дальше
      "evidence":     "...",   # на чём основано (ОБЯЗАТЕЛЬНО)
      "object_type":  "..."    # тип изменения из словаря (ОБЯЗАТЕЛЬНО)
    }

Минимум для публикации: after + mechanism + evidence + object_type.
Отсутствие after или mechanism -> REJECT: INCOMPLETE_EVENT_OBJECT.

object_type выбирается из ФАКТА изменения, а не из темы статьи:
    "voice" — не object_type. "AI" — не object_type. "startup" — не object_type.
"""
import json
import os
from datetime import datetime

# --- Словарь типов изменения (зафиксирован, расширение - только решением редактора)
OBJECT_TYPE_VOCAB = (
    "TRANSFORMATION",  # было -> стало
    "EMERGENCE",       # возникло то, чего раньше не было
    "SHIFT",           # существующее явление сместилось
    "CONFLICT",        # столкнулись две силы / модели
    "SPLIT",           # одно стало несколькими
    "CONVERGENCE",     # разное сошлось в одно
    "THRESHOLD",       # достигнута граница / появился новый порог
    "REVERSAL",        # привычное отношение перевернулось
    "INFRASTRUCTURE",  # появилась новая система / слой
    "ABSENCE",         # важно не появление, а исчезновение / непоявление
    "DEMONSTRATION",   # есть конкретная демонстрация, которую можно показать
)

# Обязательные поля EVENT_OBJECT
EVENT_REQUIRED = ("after", "mechanism", "evidence", "object_type")
EVENT_FIELDS = ("subject", "action", "before", "after", "mechanism",
                "consequence", "evidence", "object_type")

# Justification: визуальный язык one-source / one-change. Пустая строка внутри
# поля списка = «не заполнено».
_NOT_SET = object()


def event_object(concept):
    """event_object из концепта (или {})."""
    if not isinstance(concept, dict):
        return {}
    eo = concept.get("event_object") or {}
    return eo if isinstance(eo, dict) else {}


def validate_event_object(eo):
    """Коды отказа EVENT OBJECT.

    returns: [] если валиден, иначе list[str] кодов:
        INCOMPLETE_EVENT_OBJECT:<field>  - пустое обязательное поле
        UNKNOWN_OBJECT_TYPE:<value>      - object_type вне словаря
    """
    codes = []
    for f in EVENT_REQUIRED:
        v = eo.get(f, _NOT_SET)
        if v is _NOT_SET or not str(v or "").strip():
            codes.append("INCOMPLETE_EVENT_OBJECT:{}".format(f))
    ot = str(eo.get("object_type") or "").strip()
    if ot and ot not in OBJECT_TYPE_VOCAB:
        codes.append("UNKNOWN_OBJECT_TYPE:{}".format(ot))
    return codes


def object_type_of(eo):
    return str(eo.get("object_type") or "").strip()


# --- cover semantic test (детерминированные прокси)
# A/B/C/D (читаемость перехода, видимость изменения, один объект, не символ
# отрасли) — человеческий smoke-test, см. contract. E/F ниже — проверяемые.

def _visual_terms(concept):
    return " ".join(
        str(concept.get(k) or "").strip()
        for k in ("visual_object", "cover_prompt", "cover_test")
    ).strip().lower()


# Маркеры образа изменения (визуальный язык несёт переход, а не тему)
CHANGE_MARKERS = ("расщепл", "раздво", "тень", "контур", "ветв", "расход",
                  "нескол", "один", "сошл", "слива", "объедин", "стык",
                  "схож", "границ", "порог", "сдвиг", "перевер", "дверь",
                  "между", "дву", "четыре", "вместо")


def _subject_terms(concept):
    """Слова subject как «голосная» тема. Используется только для прокси E."""
    vt = _visual_terms(concept)
    return [w for w in _subject_markers() if w in vt]


def _subject_markers():
    # тематические слова отрасли: если визуальный объект = только они,
    # это «картинка про голос», а не редакционная обложка.
    return ("голос", "звук", "микрофон", "динамик", "волна", "эвц",
            "нейрос", "ai", "инструмент", "платформ", "сервис", "астола")


def cover_semantic(concept, eo):
    """E) не «банальная иллюстрация темы», F) объект совпадает с EVENT OBJECT.

    Детерминированные прокси (человеческие A/B/C/D — в contract как smoke-test):

    TOPIC_ILLUSTRATION: визуальный язык = только отра̀слевые слова (голос/звук/
    микрофон/нейросеть...) и НИ ОДНОГО маркера изменения -> «это про голос».

    SEMANTIC_MISMATCH: визуальный язык не пустой, но не несёт признака
    изменения, заявленного object_type -> cover не совпадает с EVENT OBJECT.
    """
    codes = []
    ot = object_type_of(eo)
    if not ot:
        return codes
    vt = _visual_terms(concept)
    if not vt:
        codes.append("SEMANTIC_MISMATCH:no_visual_object")
        return codes
    markers = [w for w in CHANGE_MARKERS if w in vt]
    if markers:
        return codes
    if _subject_terms(concept) or len(vt) < len("микрофон и тень"):
        codes.append("TOPIC_ILLUSTRATION")
    else:
        codes.append("SEMANTIC_MISMATCH")
    return codes


def text_cover_match(concept, eo):
    """TEXT/COVER CONSISTENCY: object_type текста = object_type EVENT OBJECT.

    returns: [] если совпадают; иначе ["TEXT_COVER_MISMATCH:object_type"].
    """
    ot_eo = object_type_of(eo)
    ot_text = str(concept.get("object_type") or "").strip()
    if ot_eo and ot_text and ot_eo != ot_text:
        return ["TEXT_COVER_MISMATCH:{}!={}".format(ot_text, ot_eo)]
    return []


# --- журнал проверки (persistent, дедуп по guid+verdict+кодам) -------------

_EDITORIAL_CACHE = {}
EDITORIAL_FILE = None  # заполняется из publisher.py (state/editorial.jsonl)


def set_editorial_file(path):
    global EDITORIAL_FILE
    EDITORIAL_FILE = path


def _hydrate():
    global _EDITORIAL_CACHE
    if _EDITORIAL_CACHE:
        return
    try:
        with open(EDITORIAL_FILE, "r", encoding="utf-8") as f:
            for ln in f:
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                g = row.get("guid")
                if g:
                    _EDITORIAL_CACHE[g] = {
                        "guid": g,
                        "editorial_object": row.get("editorial_object"),
                        "cover_semantic": row.get("cover_semantic"),
                        "text_cover_match": row.get("text_cover_match"),
                        "object_type": row.get("object_type"),
                        "cover_concept": row.get("cover_concept"),
                    }
    except OSError:
        pass


def log_editorial(guid, rec):
    """Записать ОДНУ jsonl-строку при изменении вердикта (не каждый цикл)."""
    global _EDITORIAL_CACHE
    if not EDITORIAL_FILE:
        return False
    if not _EDITORIAL_CACHE:
        _hydrate()
    key = {
        "guid": guid,
        "editorial_object": rec.get("editorial_object"),
        "cover_semantic": rec.get("cover_semantic"),
        "text_cover_match": rec.get("text_cover_match"),
        "object_type": rec.get("object_type"),
        "cover_concept": rec.get("cover_concept"),
    }
    if _EDITORIAL_CACHE.get(guid) == key:
        return False
    _EDITORIAL_CACHE[guid] = key
    try:
        out = dict(key)
        out["ts"] = datetime.now().astimezone().isoformat(timespec="seconds")
        out["event_object"] = rec.get("event_object") or {}
        out["article_structure"] = rec.get("article_structure") or []
        out["cover_path"] = rec.get("cover_path") or ""
        with open(EDITORIAL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False