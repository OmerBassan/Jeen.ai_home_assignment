# Jeen.ai Home Assignment — Omer Bassan

Submission for the **Junior AI Solution Engineer (Talk team)** role at Jeen.ai.

Two deliverables: a working Hebrew outbound voice agent for El Al, and a Python semantic search tool.

---

## Part 1 — Voice AI Agent: Dana (El Al Outbound)

An AI-powered outbound calling agent that contacts El Al passengers who haven't checked in online. Dana speaks Hebrew, handles objections, collects check-in status, and writes results back to the passenger data source — all in real time.

**Built on:** Vapi · GPT-4.1 · Deepgram Nova-3 · ElevenLabs v3

### Repository contents

| Path | Description |
|---|---|
| `System prompt.txt` | Full Hebrew system prompt with dynamic variables |
| `agent_export.json` | Vapi agent configuration export |
| `passengers - mock data.xlsx` | Mock passenger data source (≥3 rows) |
| `conversations_table.pdf` | Summary table of example calls and their written-back outcomes |
| `Recording/` | MP3 of an outbound Hebrew call + transcript |
| `Screenshots/` | Agent configuration, conversation flow, and results table |
| `additions/appscript.txt` | Google Apps Script — the webhook connecting Vapi to the data source |
| `additions/natbag description navi.txt` | Knowledge base file used by Dana (Terminal 3 navigation) |

### How it works

```text
Vapi triggers outbound call
       │
       ▼
Dana calls get_passenger_data (webhook → Google Apps Script → Google Sheet)
       │   Returns: name, flight, gate, minutes to closing, baggage, companions
       ▼
Dana conducts Hebrew conversation, handles objections and edge cases
       │
       ▼
Dana calls summarize_call before every exit point
       │   Writes: outcome, Hebrew summary, baggage offload flag → back to Sheet row
       ▼
Call ends (hangup / transfer to human)
```

### Tool functions

Dana has four tools registered in Vapi. All HTTP calls go to the Google Apps Script webhook (`additions/appscript.txt`).

#### `get_passenger_data`

Called once at the very start of every call, before Dana speaks. No arguments.

Returns the active passenger record:

| Field | Type | Example |
|---|---|---|
| `record_id` | string | `"row_4"` |
| `passenger_name` | string | `"דנה לוי"` |
| `flight_number` | string | `"LY315"` |
| `destination` | string | `"לונדון"` |
| `gate` | string | `"B14"` |
| `minutes_to_closing` | number | `22` |
| `has_checked_baggage` | string | `"Yes"` / `"No"` |
| `companions` | string | names or empty |
| `passenger_type` | string | `"Standard"` / `"Requires Assistance"` |

#### `summarize_call`

Called silently before every exit point (hangup, transfer, or farewell). Writes the outcome back to the passenger's row in the sheet.

| Parameter | Type | Description |
|---|---|---|
| `record_id` | string | From `get_passenger_data` response |
| `outcome` | string | One of the outcome codes below |
| `call_summary_he` | string | One short Hebrew sentence describing what happened |
| `baggage_offload_required` | boolean | `true` only if passenger won't board AND has checked baggage |

**Outcome codes:**

| Code | Situation |
|---|---|
| `on_the_way` | Passenger heading to gate |
| `boarded` | Already at gate |
| `third_party_only` | Refused or cancelled flight |
| `detained` | Held at security / passport control |
| `medical` | Medical issue reported |
| `passport_lost` | Lost or stolen passport |
| `transferred` | Transferred to human agent |
| `line_issue` | No answer / noisy line / tech failure |

#### `transfer_to_human`

Transfers the live call to a human El Al agent. Called after `summarize_call` in medical, lost passport, or confused-location scenarios.

#### `end_phone_call`

Explicitly ends the call. Used when there is no answer. In most flows, Vapi auto-hangs on the farewell phrase — `end_phone_call` is only invoked for the no-answer case.

### Example conversations (see `conversations_table.pdf`)

| Passenger | Scenario | Outcome |
|---|---|---|
| דנה לוי | מתפנה ובאה | `on_the_way` — אישרה הגעה |
| משה אברהם | מסרב + כבודה | `third_party_only` — סירוב, כבודה תורד (recording in `Recording/`) |
| רינה גולדברג | זקוקה לעזרה + כבודה | `transferred` — הועברה לנציג |

---

## Part 2 — Python RAG Script

A CLI tool that ingests TXT or PDF files, creates embeddings via OpenAI, and answers semantic search queries using cosine similarity.

### Setup

```bash
cd "Python Task"
pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_key_here
```

### Usage

```bash
# Ingest a file
python app.py ingest path/to/file.txt

# Query
python app.py search "your question here"
```

### Pipeline

File → extract text → overlapping chunks → embed each chunk (OpenAI `text-embedding-3-small`) → store locally in `store.json` → on query, embed the question and return top-k chunks by cosine similarity.
