import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import torch

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFacePipeline
from langchain.chains import RetrievalQA

import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global Variables & Configuration ---
# Use a smaller, faster model for embeddings
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Use a small, open-source LLM for generation
LLM_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

DOCS_PATH = "./docs"
DB_FAISS_PATH = "vectorstore/db_faiss"

# --- FastAPI App Initialization ---
app = FastAPI(title="RAG-style LLM Pipeline POC")

# --- Pydantic Models for API ---
class Query(BaseModel):
    text: str

# --- RAG Pipeline Components (Global State) ---
db = None
qa_chain = None

# --- Application Logic ---
def setup_rag_pipeline():
    """
    Initializes the RAG pipeline: loads documents, creates embeddings,
    and sets up the QA chain. This is called on application startup.
    """
    global db, qa_chain

    if not os.path.exists(DOCS_PATH) or not os.listdir(DOCS_PATH):
        logger.warning(f"'{DOCS_PATH}' directory is empty or does not exist. The RAG system will not have any documents to query.")
        return

    # 1. Load Documents
    docs = []
    for filename in os.listdir(DOCS_PATH):
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(DOCS_PATH, filename))
            docs.extend(loader.load())
    
    if not docs:
        logger.warning("No PDF documents were loaded. QA chain will not be functional.")
        return

    # 2. Split Documents into Chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(docs)

    # 3. Create Embeddings
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={'device': DEVICE})

    # 4. Create and Persist Vector Store (FAISS)
    logger.info("Creating FAISS vector store from documents...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)
    logger.info("FAISS vector store created and saved.")

    # 5. Initialize LLM
    llm = HuggingFacePipeline.from_model_id(
        model_id=LLM_MODEL_NAME,
        task="text-generation",
        device_map="auto",  # Use "auto" to leverage GPU if available
        pipeline_kwargs={
            "max_new_tokens": 256,
            "top_p": 0.95,
            "temperature": 0.1,
            "repetition_penalty": 1.15
        },
    )

    # 6. Create QA Chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={'k': 2}),
        return_source_documents=True
    )
    logger.info("RAG pipeline setup complete.")

@app.on_event("startup")
def startup_event():
    """
    On startup, create and load the RAG pipeline components.
    """
    setup_rag_pipeline()


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def read_root():
    """
    A simple HTML form to interact with the RAG endpoint.
    """
    html_content = """
    <html>
        <head>
            <title>RAG POC</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                form { margin-bottom: 20px; }
                input[type="text"] { width: 500px; padding: 8px; }
                input[type="submit"] { padding: 8px 12px; }
                .result { margin-top: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>RAG-style LLM Pipeline (Mini POC)</h1>
            <p>Enter a query about the content in the uploaded PDF documents.</p>
            <form action="/query" method="post">
                <input type="text" name="text" placeholder="e.g., What is Artificial Intelligence?">
                <input type="submit" value="Ask">
            </form>
            <div id="response"></div>
            <script>
                document.querySelector('form').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    const query = e.target.elements.text.value;
                    const responseDiv = document.getElementById('response');
                    responseDiv.innerHTML = 'Thinking...';
                    
                    const response = await fetch('/query-api', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: query })
                    });
                    
                    const result = await response.json();
                    
                    if(response.ok) {
                        responseDiv.innerHTML = `<div class="result"><h2>Answer:</h2><p>${result.answer}</p><h3>Sources:</h3><p><pre>${JSON.stringify(result.sources, null, 2)}</pre></p></div>`;
                    } else {
                        responseDiv.innerHTML = `<div class="result" style="background-color: #fdd;"><h2>Error:</h2><p>${result.detail}</p></div>`;
                    }
                });
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/query-api", tags=["API"])
async def handle_query(query: Query):
    """
    Handles a query by retrieving relevant context and generating an answer.
    """
    if not qa_chain:
        raise HTTPException(status_code=503, detail="RAG pipeline is not available. Check server logs for errors during setup.")
    
    logger.info(f"Received query: {query.text}")
    try:
        result = qa_chain.invoke({"query": query.text})
        answer = result.get('result')
        sources = [
            {"source": doc.metadata.get('source', 'N/A'), "page": doc.metadata.get('page', 'N/A')} 
            for doc in result.get('source_documents', [])
        ]
        return {"answer": answer, "sources": sources}
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the query.")
