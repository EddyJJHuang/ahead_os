# Meridian Fleet API — Product Documentation (Public, v3)

The Meridian Fleet API lets customers manage autonomous-robot fleets programmatically.
Base URL: `https://api.meridian.example/v3`. All requests require a Bearer token.

## Authentication
Send `Authorization: Bearer <API_KEY>`. Tokens are scoped per project. Rate limit:
600 requests/minute per token; bursts return HTTP 429 with `Retry-After`.

## Resource: Robots
- `GET /robots` — list robots. Query params: `status` (idle|active|charging|fault),
  `site_id`, `page`, `page_size` (max 200).
- `GET /robots/{robot_id}` — fetch one robot, including battery %, firmware, and
  last telemetry timestamp.
- `POST /robots/{robot_id}/commands` — issue a command. Body: `{ "command":
  "recall" | "pause" | "resume", "reason": "<string>" }`.

## Resource: Tasks
- `GET /tasks` — list tasks. Filter by `state` (queued|running|done|failed).
- `POST /tasks` — create a task. Body: `{ "robot_id": "...", "type": "pick" |
  "transport" | "inspect", "payload": { ... } }`.

## Resource: Telemetry
- `GET /telemetry?robot_id=...&since=<iso8601>` — stream of telemetry points.
  Each point has `battery_pct`, `temp_c`, `error_code` (nullable), `position`.

## Error Model
Errors return `{ "error": { "code": "<machine_code>", "message": "<human text>" } }`.
Common codes: `rate_limited` (429), `not_found` (404), `invalid_command` (422),
`robot_in_fault` (409 — robot must be cleared before new commands).

## Webhooks
Register a webhook to receive `robot.fault`, `task.completed`, and `task.failed`
events. Payloads are signed with HMAC-SHA256 in the `X-Meridian-Signature` header.
