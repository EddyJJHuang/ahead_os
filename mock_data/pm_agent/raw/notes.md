# BriefOS Product Notes

BriefOS is a local-first AI chief of staff for workspace context.

## Core idea

Most AI assistants are reactive. They wait for the user to ask a question.

BriefOS is proactive. It continuously reads workspace data such as emails, Slack messages, calendar events, tasks, and notes, then prepares daily briefings, meeting prep, and follow-up drafts.

## Why local-first matters

Workspace data is sensitive. Founders, operators, and technical teams often have confidential information in their emails, calendars, customer notes, and internal Slack messages.

BriefOS should be able to run locally so that private context does not need to leave the user's machine.

## Hackathon architecture

Current local development stack:

- Next.js frontend
- FastAPI backend
- Chroma vector database
- Ollama or OpenAI for model calls
- Local JSON and Markdown files as fake workspace data

Hackathon swap:

- Replace Ollama with Nemotron
- Replace custom agent loop with OpenClaw
- Replace local Python tool execution with OpenShell

## Demo flow

1. Generate Daily Brief
2. Open Dell x NVIDIA Architecture Review meeting
3. Generate Meeting Prep
4. Ask: "What decision do I need to make before this meeting?"
5. Generate follow-up draft

## Key message

BriefOS is not another chatbot. It is a private, local operating layer for work context.