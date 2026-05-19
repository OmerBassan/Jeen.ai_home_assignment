# Voice Agent Architecture — Jeen.ai Home Assignment

## Use Case
Airport outbound voice agent. Calls Hebrew-speaking passengers who checked in but haven't boarded, reminding them their gate is closing soon. Built on **Vapi** + **Google Apps Script** + **Google Sheets**.

---

## Google Sheets Schema

### Sheet 1: `passengers`
| Column | Notes |
|---|---|
| record_id | Numeric ID, primary key |
| passenger_name | Full name |
| flight_number | e.g. LY315 |
| destination | City name |
| gate | e.g. B14 |
| gate_closing_time | ISO datetime |
| phone_number | E.164 format |
| has_checked_baggage | TRUE/FALSE |
| companions | Name of traveling companion, or empty |
| passenger_type | `standard`, `unaccompanied_minor`, `requires_assistance` |
| checked_in | TRUE/FALSE |
| boarded | TRUE/FALSE |

**Total records: 10** test passengers across multiple flights and gates.

---

### Sheet 2: `late_passengers`
| Column | Notes |
|---|---|
| record_id | Copied from `passengers` on injection |
| passenger_name | Copied on injection |
| flight_number | Copied on injection |
| destination | Copied on injection |
| gate | Copied on injection |
| gate_closing_time | Copied on injection |
| phone_number | Copied on injection |
| has_checked_baggage | Copied on injection |
| companions | Copied on injection |
| passenger_type | Copied on injection |
| call_attempts | Integer, starts at 0 |
| call_summary | Written back by Apps Script from Vapi structured output |
| call_status | `pending`, `in_progress`, `resolved`, `no_answer`, `escalated` |
| last_updated | Timestamp of last write |
| baggage_offload_required | TRUE/FALSE, set when passenger refuses to board |
| last_call_time | Timestamp of last call attempt |
| injected_at | Timestamp of injection |

### Sheet 3: `config`
Key-value store used by Apps Script for named ranges (`current_passenger`), per-call state (`call_<callId>`), trigger tracking, and radar logs.

---

## Google Apps Script Backend

All backend logic runs as a single Apps Script project deployed as a Web App (doPost endpoint). Vapi points its Server URL at this deployment.

**Entry point — `doPost(e)`**: Routes incoming Vapi webhooks by `message.type`:
- `assistant-request` → `handleAssistantRequest` (used for API-initiated calls)
- `tool-calls` → `handleToolCall` (used when Dana invokes `get_passenger_data` or `summarize_call` mid-call)
- `end-of-call-report` → `handleEndOfCall` (fallback writeback if tool didn't run)

### Injector — `injectLatePassengers()` (runs every minute via time-based trigger)
Scans `passengers` sheet for rows where `checked_in=TRUE`, `boarded=FALSE`, and gate closes within the next 15 minutes. Passengers not already in `late_passengers` are appended. Priority order at injection: `unaccompanied_minor` (0) → `requires_assistance` (1) → `standard` (2). These passenger types are still injected but are never sent to Vapi — ground crew handles them directly.

### Picker — `pickCurrentPassenger()` (runs every minute via time-based trigger)
Scans `late_passengers` for eligible rows (`call_attempts < 2`, `call_status` is `pending` or blank, `unaccompanied_minor` excluded). Sorts by: minutes to gate close → passenger type priority → baggage flag. Writes the winning `record_id` to the `current_passenger` named range so Dana can retrieve it mid-call.

### Tool handler — `handleToolCall`
**`get_passenger_data`**: Reads `current_passenger` named range, finds the row in `late_passengers`, marks it `in_progress`, stamps `last_call_time`, and returns a normalized passenger object to Vapi (all fields Dana needs: name, flight, destination, gate, minutes to closing, baggage, companions, passenger type). Also stashes a `call_<callId> → record_id` mapping in `config` so the row can be found even if the named range is overwritten mid-call.

**`summarize_call`**: Receives `record_id`, `outcome`, `call_summary_he`, and `baggage_offload_required` from Dana. Writes `call_status` (`resolved` / `escalated` / `no_answer`), `call_summary`, `baggage_offload_required`, increments `call_attempts`, and resets `current_passenger` to 0. Then calls the Vapi API to end the call (`PATCH /call/<callId>` with `status: ended`).

### End-of-call fallback — `handleEndOfCall`
Fires when Vapi sends the `end-of-call-report` event. If `summarize_call` already wrote a summary, skips overwrite and just clears `current_passenger`. If the call dropped before the tool ran (user hung up, timeout), writes `call_status` from `endedReason` and schedules a 25-second delayed trigger (`fetchAnalysisAndFinalize`) to fetch Vapi's transcript-based analysis as a fallback summary.

---

## Vapi Agent ✅ CONFIGURED
- Agent name: **Dana (דנה)** — El Al outbound voice agent
- System prompt: `System prompt.txt`
- First message: set directly in Vapi First Message field (not in system prompt) — uses plural Hebrew (`איפה אתם?`) for gender-neutral addressing
- Language: Hebrew ONLY — responds to English speakers in Hebrew: "אני מצטערת, אני מדברת רק עברית"
- **STT:** Deepgram Nova-3 (fallback: Whisper v3)
- **LLM:** GPT-4.1 (fallback: GPT-4o)
- **TTS:** ElevenLabs v3 (fallback: Azure TTS he-IL-HilaNeural)
- **Knowledge file:** `natbag description navi.txt` — Ben Gurion Terminal 3 navigation matrix
- **Server URL:** Workflow 3 webhook URL (end-of-call events only)
- **Max call duration:** 120 seconds (Vapi-enforced hard cap — prevents stalling loops)
- **Tools configured:**
  - `end_phone_call` — Function tool, no webhook
  - `transfer_to_human` — Transfer Call tool, destination: ground crew number
- **Dynamic variables:** `passenger_name`, `flight_number`, `destination`, `gate`, `minutes_to_closing`, `has_checked_baggage`, `companions`
- **Structured output schema** (extracted at end-of-call, posted to WF3 webhook):
  - `outcome` — enum: `made_it`, `on_the_way`, `wont_make_it_time`, `refused`, `cancelled`, `detained`, `medical`, `passport_lost`, `third_party_only`, `line_issue`, `transferred`
  - `call_summary_he` — 1–2 sentence Hebrew summary of what happened
  - `final_status_he` — exact Hebrew status line for the dashboard
  - `baggage_offload_required` — boolean
  - `companion_missing` — boolean
  - `third_party_pickup` — boolean

---

## Current Status
- [x] Airtable schema designed and built
- [x] 29 test passengers loaded
- [x] Workflow 1 — complete and working (with conditional escalation at injection)
- [x] Workflow 2 — complete (all 5 nodes configured and working)
- [x] Vapi assistant — STT, LLM, TTS, functions, knowledge file, server URL all configured
- [x] Workflow 3 — complete (webhook + Route by Outcome on structured `outcome` + 3 Mark nodes with retry logic on Mark No Answer)
- [x] Vapi structured-output schema configured (replaces mid-call `update_dashboard` tool)
- [ ] End-to-end test + submission assets — see Plan below

---

## Plan to Finish

Principle: **everything below is what the assignment requires. Nothing more.** No new features, no extra workflows, no infrastructure polish. We're done building — we're now testing, recording, and packaging.

### Phase 1 — End-to-End Test (Part 1 validation)
Goal: prove the full chain works once, with a real call to my phone.

1. Activate all 3 workflows in n8n
2. Confirm Vapi Server URL points at WF3 webhook (production URL, not test URL)
3. Pick one passenger row in `Active_late_passengers` and replace its `phone_number` with `+972525407580` temporarily
4. Wait for WF2 to fire (within 1 minute) — phone should ring
5. Answer in Hebrew, let Dana run through the flow
6. Verify after the call:
   - `call_status` flipped to `in_progress` mid-call, then to final outcome (`resolved`/`no_answer`/`escalated`)
   - `call_summary` populated by Vapi's end-of-call summary
   - `call_attempts` incremented
7. If anything fails, fix the smallest possible thing and retry. No refactors.

### Phase 2 — Capture Submission Assets (Part 1)
Goal: collect the artifacts the assignment lists in section 3.

| Asset | How | Required by |
|---|---|---|
| Hebrew call recording (MP3/MP4) | Download from Vapi call logs after Phase 1 test | 3.3, 1.4.9 |
| 3+ rows with summaries (≥1 successful) | Run 3 more calls to my phone, vary scenarios (resolve, refuse with baggage, no_answer by ignoring the call) | 1.4.8 |
| `agent_prompt.txt` | Rename existing `System prompt.txt` → `agent_prompt.txt` | 3.4 |
| `agent_export.json` | Export from Vapi dashboard → save in repo root | 3.5 |
| Data source export | Airtable view link OR CSV export of `Active_late_passengers` | 3.6 |
| Screenshots (3): Vapi assistant config, n8n workflow canvas, Airtable results table | Manual | 3.7 |
| `recordings/` folder | Drop call MP3s here | 3.3 |

### Phase 3 — Part 2: Python RAG Script
Goal: build the minimum CLI that satisfies section 2.1–2.8. No web UI, no fancy storage, no chunking strategies beyond fixed-size overlap.

Files to create per CLAUDE.md spec:
- `main.py` — Click/argparse CLI with `ingest` and `search` commands
- `chunker.py` — extract text from TXT/PDF (use `pypdf`), split into ~500-char chunks with 50-char overlap
- `embedder.py` — wrap OpenAI `text-embedding-3-small` (default) — skip Gemini to halve the scope
- `store.py` — JSON file at `./store.json` with list of `{text, embedding}` entries
- `search.py` — cosine similarity, return top-k=3
- `.env.example` — `OPENAI_API_KEY=`
- `requirements.txt` — `openai`, `pypdf`, `python-dotenv`, `numpy`, `click`

Test by ingesting `natbag description navi.txt` and searching for "איפה שירותים בטרמינל 3" — should return the bathrooms chunk.

### Phase 4 — Package & Submit
1. `README.md` — one section per part:
   - Part 1: architecture diagram (link to this file), how to run the n8n workflows, Vapi config notes
   - Part 2: install + usage commands (already drafted in CLAUDE.md, lift them)
2. Presentation (4–6 slides, PDF):
   - Slide 1: Problem + 2 use cases (outbound late-passenger reminder ← chosen; inbound flight-status hotline)
   - Slide 2: Why outbound + business value (reduce gate-delay incidents, baggage offload cost savings, ground-crew time freed)
   - Slide 3: Model comparison table (STT: Whisper v3 vs Deepgram Nova-3 vs Azure he-IL; LLM: GPT-4.1 vs GPT-4o vs Claude Sonnet 4.5; TTS: ElevenLabs Turbo v2.5 vs Azure HilaNeural) — see `model_decisions.md`
   - Slide 4: Architecture diagram (Airtable → n8n WF1/WF2 → Vapi → WF3 → Airtable)
   - Slide 5: Demo screenshots + Hebrew call summary excerpt
   - Slide 6 (optional): ROI / next steps
3. Push everything to GitHub. Make sure `.env` is `.gitignored`.

### Out of scope (do NOT do)
- Real outbound dialing infrastructure beyond test calls
- Connecting a real DID/phone number to Vapi
- Gemini support in the Python script
- SQLite or vector DB — JSON is fine
- Web UI for anything
- Additional n8n workflows
- Refactoring the existing workflows
- Migrating Airtable → Google Sheets (already evaluated, not worth the rebuild)

### Order of work
Phase 1 → Phase 2 (interleaved — each test call also captures recording/row) → Phase 4 README/repo skeleton → Phase 3 Python script → Phase 4 presentation → submit.
