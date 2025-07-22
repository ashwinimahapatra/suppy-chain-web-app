import os
import wikipedia
from sec_edgar_downloader import Downloader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

VECTOR_DB_DIR = "chroma_db"
CHROMA_COLLECTION = "supply_chain"
EDGAR_SAVE_DIR = "downloads"
EMBED_MODEL = "all-MiniLM-L6-v2"

model = SentenceTransformer(EMBED_MODEL)
client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=VECTOR_DB_DIR))
collection = client.get_or_create_collection(name=CHROMA_COLLECTION)

def fetch_wikipedia_summary(company):
    try:
        return wikipedia.summary(company, sentences=5)
    except:
        return ""

def fetch_10k_filings(company):
    dl = Downloader(EDGAR_SAVE_DIR)
    try:
        dl.get("10-K", company, amount=1)
    except:
        pass

def read_10k_text(company):
    folder = os.path.join(EDGAR_SAVE_DIR, "sec-edgar-filings")
    for d in os.listdir(folder):
        if d.lower() in company.lower():
            company_dir = os.path.join(folder, d)
            break
    else:
        return ""
    texts = []
    for root, _, files in os.walk(company_dir):
        for file in files:
            if file.endswith(".txt"):
                with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                    texts.append(f.read())
    return "\n".join(texts)

def embed_chunks_and_store(company, text):
    chunks = [text[i:i+512] for i in range(0, len(text), 512)]
    embeddings = model.encode(chunks)
    for i, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            metadatas=[{"company": company}],
            ids=[f"{company}_{i}"],
            embeddings=[embeddings[i]]
        )

def extract_supply_chain_for_company(company):
    wiki_text = fetch_wikipedia_summary(company)
    fetch_10k_filings(company)
    sec_text = read_10k_text(company)
    full_text = wiki_text + "\n" + sec_text
    embed_chunks_and_store(company, full_text)

    query = f"List suppliers and customers of {company}"
    results = collection.query(query_texts=[query], n_results=5)
    text_context = "\n".join(results["documents"][0])

    suppliers, customers = [], []
    for line in text_context.split("\n"):
        if "supplier" in line.lower() or "supply" in line.lower():
            suppliers.append(line.strip())
        if "customer" in line.lower() or "retail" in line.lower() or "sell to" in line.lower():
            customers.append(line.strip())
    return {"suppliers_raw": suppliers, "customers_raw": customers}
