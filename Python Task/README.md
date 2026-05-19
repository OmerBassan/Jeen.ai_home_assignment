# Simple Python Text Embeddings & Search

A CLI tool that ingests TXT or PDF files, generates embeddings via OpenAI, persists them locally, and answers semantic search queries using cosine similarity.

## Features

- Extract text from `.txt` and `.pdf` files
- Word-level chunking with configurable overlap
- Embeddings via OpenAI `text-embedding-3-small`
- Local persistence to `store.json` (ingest once, search many times)
- Source tracking per chunk
- Configurable `--top-k` for search results

## Project Structure

```text
Python Task/
├── .env                  # API key (not committed)
├── .gitignore
├── requirements.txt
├── app.py                # CLI entry point
├── store.json            # Local vector store (created on first ingest)
└── README.md
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your OpenAI key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Ingest a file

```bash
python app.py ingest path/to/file.txt
python app.py ingest path/to/document.pdf
```

Each ingest appends to `store.json` — you can ingest multiple files.

### Search

```bash
python app.py search "your question here"
python app.py search "your question" --top-k 5
```

Returns the top-k chunks ranked by cosine similarity, each with its similarity score and source file.

## How it works

```text
File → extract text → split into overlapping chunks → embed each chunk
                                                          │
                                                          ▼
                                                    store.json
                                                          │
Query → embed → cosine similarity vs. stored embeddings → top-k chunks
```
