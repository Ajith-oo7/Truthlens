# FlutterFlow screen mapping

TruthLens FlutterFlow cannot be generated from this repo. Rebuild these screens against the same API.

## App state

- `apiBase` (string, default `http://localhost:8080`)
- `factCheckId` (string)
- `dossier` (JSON)
- `events` (list)

## Screens

| FlutterFlow page | Route | API |
| --- | --- | --- |
| Splash | `/splash` | none |
| Home | `/` | `POST /v1/fact-checks`, `POST /v1/fact-checks/screenshot` |
| Processing | `/processing/:id` | `GET /v1/fact-checks/{id}/events` |
| Result | `/result/:id` | `GET /v1/fact-checks/{id}` |
| History | `/history` | `GET /v1/fact-checks` |
| Analytics | `/analytics` | `GET /v1/analytics/summary` |

## Design

Import tokens from [docs/stitch/DESIGN_TOKENS.md](../stitch/DESIGN_TOKENS.md). Inter + JetBrains Mono, dark surfaces, cyan primary, semantic verdict chips.

## Actions

1. Home Verify → POST claim → set `factCheckId` → navigate Processing.
2. Processing → SSE until `completed` → navigate Result.
3. History row tap → navigate Result with that id.
