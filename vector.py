# Imports and warnings.
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
import os
from tqdm import tqdm
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
#--------------------------------------------------------------------------------------------

DATA_DIR = "data"                 # Folder containing your lecture PDFs & PPTXs
DB_DIR = "vector_db"              # Output folder for vector database
EMBED_MODEL = "nomic-embed-text"  # Ollama model for embeddings
CHUNK_SIZE = 1000                 # Max characters per chunk
CHUNK_OVERLAP = 200               # Overlap between chunks


def load_documents():
    """Load all PDF and PPTX files from the data folder."""
    docs = []
    for root, _, files in os.walk(DATA_DIR):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(path)
            elif filename.lower().endswith(".pptx"):
                loader = UnstructuredPowerPointLoader(path)
            else:
                continue

            print(f"📄 Loading: {filename}")
            try:
                docs.extend(loader.load())
            except Exception as e:
                print(f"⚠️ Skipped {filename}: {e}")
    return docs


def build_vector_store():
    """Create embeddings and persist them to Chroma with progress bar."""
    print("📚 Loading lecture files...")
    documents = load_documents()
    if not documents:
        print("❌ No documents found in /data. Please add your PDFs or PPTXs first.")
        return

    print("✂️ Splitting text into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} text chunks.\n")

    print(f"🧠 Generating embeddings with Ollama model: {EMBED_MODEL}")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)

    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]

    embedded_texts = []
    for text in tqdm(texts, desc="🔢 Creating embeddings", ncols=100):
        embedded_texts.append(text)

    print("\n💾 Building Chroma vector database...")
    db = Chroma.from_texts(embedded_texts, embeddings, metadatas=metadatas, persist_directory=DB_DIR)
    db.persist()

    print(f"✅ Vector database successfully saved to: {DB_DIR}\n")


def get_retriever(search_k: int = 5):
    """Load the existing Chroma vector DB and return a retriever."""
    if not os.path.exists(DB_DIR):
        raise FileNotFoundError("❌ No vector DB found.")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    return db.as_retriever(search_type="similarity", search_kwargs={"k": search_k})


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    build_vector_store()
