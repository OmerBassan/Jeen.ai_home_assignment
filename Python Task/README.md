# Simple Python Text Embeddings & Search

A simple Python utility that extracts text from TXT or PDF files, splits the text into semantic chunks, generates embeddings using the OpenAI API, and allows querying the text using Cosine Similarity.

## Features
- Extract text from `.txt` and `.pdf` files.
- Chunk text with customizable sizes and overlap.
- Generate embeddings via OpenAI's `text-embedding-3-small`.
- Simple in-memory semantic search using Cosine Similarity.

## Project Structure
```text
python-embeddings-task/
│
├── .env                  # API keys and secrets (Do not commit!)
├── .gitignore            # Tells Git which files to ignore
├── requirements.txt      # Project dependencies
├── app.py                # Main application script
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-url>
   cd python-embeddings-task
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**
   Create a `.env` file in the root directory of the project and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the script:**
   ```bash
   python app.py
   ```