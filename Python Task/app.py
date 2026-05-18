import os
from dotenv import load_dotenv
from pypdf import PyPDFReader
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Missing OpenAI API Key! Please check your .env file.")

client = OpenAI(api_key=api_key)


def extract_text(file_path):
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_path.endswith('.pdf'):
        reader = PyPDFReader(file_path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    else:
        raise ValueError("Unsupported file format. Use .txt or .pdf")


def split_text_into_chunks(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


class SimpleVectorStore:
    def __init__(self):
        self.chunks = []
        self.embeddings = []

    def process_and_store(self, file_path):
        print(f"Reading file: {file_path}...")
        raw_text = extract_text(file_path)

        print("Splitting text into chunks...")
        self.chunks = split_text_into_chunks(raw_text)

        print(f"Creating embeddings for {len(self.chunks)} chunks...")
        self.embeddings = [get_embedding(chunk) for chunk in self.chunks]
        print("Done! Data stored in memory.")

    def search(self, query, top_k=1):
        if not self.embeddings:
            return "No data stored yet."

        query_embedding = np.array(get_embedding(query)).reshape(1, -1)
        db_embeddings = np.array(self.embeddings)

        similarities = cosine_similarity(query_embedding, db_embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "chunk": self.chunks[idx],
                "score": similarities[idx]
            })
        return results


if __name__ == "__main__":
    test_file = "sample.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Python is an interpreted, high-level, general-purpose programming language. "
                "Created by Guido van Rossum and first released in 1991. "
                "The OpenAI API allows developers to access powerful AI models for text generation and embeddings. "
                "An embedding is a vector (list of numbers) representing the semantic meaning of a text.")

    store = SimpleVectorStore()
    store.process_and_store(test_file)

    question = "Who created Python and when?"
    print(f"\nUser Question: '{question}'")

    search_results = store.search(question, top_k=1)
    print("\n--- Most Relevant Chunk Found ---")
    print(f"Score: {search_results[0]['score']:.4f}")
    print(f"Content: {search_results[0]['chunk']}")
