# PM Agent Fake Data

Put the launch-readiness fake data files from Google Drive in `raw/`:

- `calender.json`
- `customers.json`
- `emails.json`
- `github.json`
- `jira.json`
- `notes.md`
- `product_docs.md`
- `sample_expected_brief.txt`
- `slack.json`
- `tasks.json`

Then run:

```bash
python build_pm_index.py
```

The builder regenerates `docs/pm_workspace.md` from the raw files, then indexes
`docs/*.md` and `playbook/*.md` into `pm_rag_index.faiss` and
`pm_rag_chunks.json`.

## Optional Live Google Workspace Data

For a more impressive local demo, you can ingest read-only Google Workspace
context into a private, gitignored directory:

```bash
python scripts/google_ingest.py --days 14 --query "launch OR checkout OR blocker"
python build_pm_index.py
```

The script writes private snapshots to:

```text
mock_data/pm_agent/live/
```

That directory is ignored by git. Do not commit OAuth files or live workspace
data:

```text
credentials.json
token.json
mock_data/pm_agent/live/
```

Google APIs to enable in Google Cloud:

- Gmail API
- Google Calendar API
- Google Tasks API
- Google Meet API, optional

The ingest script uses read-only scopes where possible and redacts obvious email
addresses and phone numbers before writing JSON. Keep the query narrow for demos.
