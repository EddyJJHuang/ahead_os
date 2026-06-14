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
