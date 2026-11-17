# AI Visibility Queue Planner

The queue planner turns a frozen query module into an explicit, auditable execution matrix. It is an offline planning tool: it does not call providers, infer region access, or create observations.

## Generate a queue

```bash
python tools/ai_visibility_queue.py generate \
  --module research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json \
  --output research/queues/ru-generic-discovery-queue.csv

python tools/ai_visibility_queue.py generate \
  --module research/ai-visibility-benchmark-queries-2026-11-17.json \
  --output research/queues/ru-brand-service-queue.csv
```

For the current RU modules, the expected Cartesian products are 29 prompts × 12 platform surfaces (348 planned rows) for generic discovery, and 20 prompts × 12 platform surfaces (240 planned rows) for brand/service verification. Counts are derived from the source files; the tool does not hard-code them.

## Validate coverage

```bash
python tools/ai_visibility_queue.py validate \
  --queue research/queues/ru-generic-discovery-queue.csv \
  --module research/ai-visibility-ru-generic-discovery-queries-2026-11-17.json
```

Validation checks required fields, duplicate IDs and query/platform pairs, legal measurement modes, planned-state integrity, and complete Cartesian coverage against the frozen source module.

## Safety and interpretation

- Every generated row starts as `NOT_TESTED`; region verification starts as `UNVERIFIED`.
- The planner does not treat the user's current location, a provider's nominal country list, or a proxy as proof of actual test region.
- `consumer_ui`, `model_api`, and `search_results_ui` remain separate measurement modes.
- Generic-discovery prompts are checked for accidental brand/domain hints when the source marks them as unbranded.
- Queue CSVs are not benchmark observation CSVs. Do not pass them to `ai_visibility_benchmark.py`; only completed, evidence-linked observations belong there.
- The source query modules are immutable experiment definitions once collection begins. Create a new version rather than editing prompts after observations exist.
- No network, AI API, paid tracker, Firecrawl credits, website access, or website modification is used.

## Tests

```bash
python -m unittest tools.tests.test_ai_visibility_queue -v
```
