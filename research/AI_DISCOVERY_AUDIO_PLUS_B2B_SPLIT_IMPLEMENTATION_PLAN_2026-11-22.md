# Audio+ / B2B split — implementation plan (DRAFT, not for merge)

Status: DRAFT awaiting owner conditions. Derived from the merged #76 route-boundary
audit; this document only fixes the implementation contract. No generator code,
prices or site content are changed here.

## Blocked on owner decisions (from #76/#78 evidence)

1. Confirmed current Audio+ terms (prices, scope, turnaround) as the B2C product source of truth.
2. Fate of the seven historical static GEO answer pages (keep/rewrite per the #79 disposition).
3. Whether the corporate radio-production route keeps any self-serve entry point at all.

## Generator changes (tools/build_geo_site.py + registry)

1. Add an explicit `product_type` dimension to the price/service registry entries:
   `audio_plus_self_serve` vs `professional_project` — one entry cannot be both.
2. Route eligibility: registry entries with `product_type=audio_plus_self_serve` may
   feed ONLY the Audio+ product surfaces (own product pages/FAQ); they are excluded
   from the B2B commercial hub, OfferCatalog output and professional-route FAQs.
3. Professional-route pages must not embed Audio+ FAQ blocks or Audio+ prices;
   shared FAQ snippets are split into product-scoped partials.
4. The generic commercial hub lists only `professional_project` entries, each with
   the explicit scope/turnaround/negotiation boundary the #76 audit requires.
5. Historical pages: handled per owner decision above; no redirects or deletions
   are performed in this branch.

## Acceptance criteria (before this branch can leave draft)

- Validator extension: no registry entry feeds both product types (fail closed).
- Generated site diff review: no Audio+ price appears on any professional route
  page and vice versa.
- registry unit tests extended per the #75 pattern (offline fixtures).
- Owner sign-off on the three blocked decisions, recorded in this file.
