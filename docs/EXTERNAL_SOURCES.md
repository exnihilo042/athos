# External Sources Integrated Into ATHOS

ATHOS imports useful external ideas as small, testable native modules. It does
not bulk-copy incompatible projects.

## Implemented

- `fathah/hermes-desktop`: Python SSE parser in `core/sse_parser.py`, plus model/provider/profile registry pattern in `core/model_profiles.py`.
- `garrytan/gbrain`: provenance, facts-vs-takes, compiled truth plus append-only timeline in `core/truth_ledger.py`.
- `garrytan/gstack`: situational review pipeline in `core/review_pipeline.py`.
- Academic references: blackboard control, free-energy/prediction-error framing, and W3C PROV provenance are recorded in `core/external_sources.py`.

## ATHOS Policy

- Keep ATHOS as the identity; external engines and projects are capability inputs.
- Use source attribution for every imported pattern.
- Prefer compact native modules with tests over full repo imports.
- Keep paid/ambiguous API providers blocked by default under zero-spend policy.
- Make missing connectors visible as exact gaps in `/api/model_profiles` and `/api/capability_graph`.

## API Surfaces

- `POST /api/external_sources`
- `POST /api/model_profiles`
- `POST /api/review_pipeline`
- `POST /api/truth_ledger/scan`
- `POST /api/sse/parse`
