# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a home assignment for the **Jeen.ai Junior AI Solution Engineer (Talk team)** role. It has two deliverables:

1. **Part 1 — Voice AI Agent**: A working outbound Hebrew voice agent built on Vapi / Retell AI / Bland AI, plus a business analysis presentation.
2. **Part 2 — Python RAG Script**: A CLI tool that ingests TXT/PDF files, creates embeddings via OpenAI or Gemini, stores chunks locally, and answers semantic search queries.

---

## Part 2: Python RAG Script

### Running the script

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest a file (builds embeddings and stores chunks)
python main.py ingest <path/to/file.txt|pdf>

# Query
python main.py search "<your question>"
```

### Environment variables (`.env`)

```
OPENAI_API_KEY=...
# or
GEMINI_API_KEY=...
```

### Architecture

```
main.py          — CLI entry point (ingest / search commands)
embedder.py      — Calls OpenAI/Gemini embeddings API
chunker.py       — Text extraction (TXT + PDF) and chunking logic
store.py         — Persists chunks + embeddings to a local JSON/sqlite file
search.py        — Cosine similarity search over stored embeddings
.env             — API keys (never committed)
```

**Data flow**: file → extract text → split into overlapping chunks → embed each chunk → store `{chunk_text, embedding}` entries → on query, embed the question and return the top-k chunks by cosine similarity.

---

## Part 1: Voice Agent

The agent is built and configured on the chosen platform (Vapi/Retell/Bland). The relevant files committed to this repo are:

- `agent_prompt.txt` — The full system prompt used by the agent
- `agent_export.json` — Platform JSON export of the agent configuration
- `data_source.json` (or link to Google Sheet/Airtable) — Mock customer data with ≥3 rows including `call_summary` field written back after each call
- `recordings/` — MP3/MP4 of at least one Hebrew outbound conversation

### Voice agent hard requirements

- **Hebrew only** — all speech and prompts
- **≥3 dynamic variables** injected per call (e.g., `{{customer_name}}`, `{{appointment_date}}`, `{{insurance_type}}`)
- Variables pulled from the data source at call start
- Conversation summary written back to the same data source row after the call ends
- At least 3 example rows in the data source table (≥1 successful conversation)

---

## Submission Checklist

- [ ] `presentation.pdf` — 4–6 slides (use cases, model comparison, architecture, business value)
- [ ] GitHub repo (this repo) with README
- [ ] `recordings/` — Hebrew outbound call MP3/MP4
- [ ] `agent_prompt.txt`
- [ ] `agent_export.json`
- [ ] Data source with ≥3 example conversations + summaries
- [ ] Screenshots: agent config, conversation flow, results table

## Evaluation Focus

Jeen evaluates: product thinking, prompt quality, voice UX, code quality, AI understanding, creativity.
