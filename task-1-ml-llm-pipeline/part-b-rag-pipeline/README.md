# Task 1, Part B: RAG-style LLM Pipeline (Mini POC)

This project is a Proof-of-Concept for a Retrieval-Augmented Generation (RAG) system. It uses a small, open-source LLM and a local vector database to answer questions about documents provided in PDF format.

## Architecture Overview

1.  **Document Ingestion**: On startup, the application scans the `./docs` directory for PDF files.
2.  **Chunking**: It uses `LangChain`'s `PyPDFLoader` to load the text and `RecursiveCharacterTextSplitter` to break it into smaller, manageable chunks.
3.  **Embedding & Indexing**: Each text chunk is converted into a numerical vector (embedding) using the `all-MiniLM-L6-v2` model. These embeddings are stored in a `FAISS` vector database in memory and also saved to disk.
4.  **Retrieval**: When a user submits a query, the system embeds the query and uses FAISS to find the most semantically similar text chunks from the indexed documents.
5.  **Generation**: The retrieved chunks (context) and the original query are formatted into a prompt and sent to a small LLM (`TinyLlama-1.1B`). The LLM generates an answer based on the provided context.
6.  **API**: The entire workflow is exposed via a `FastAPI` endpoint, with a minimal HTML frontend for easy interaction.

## How to Run

### Prerequisites

-   Docker and Docker Compose
-   A PDF document for querying.

### Steps

1.  **Add a Document**: Place at least one `.pdf` file inside the `task-1-ml-llm-pipeline/part-b-rag-pipeline/docs/` directory.

2.  **Build and Run the Docker Container**: Navigate to the `task-1-ml-llm-pipeline/part-b-rag-pipeline/` directory and run the following command:
    ```bash
    docker build -t rag-pipeline-poc .
    docker run -p 8001:8001 rag-pipeline-poc
    ```
    *(Note: If you have an NVIDIA GPU and have the NVIDIA Container Toolkit installed, you can enable GPU access for faster performance by adding `--gpus all` to the `docker run` command.)*

3.  **Wait for Model Download**: The first time you run this, it will download the embedding and LLM models, which can be several gigabytes. This may take a significant amount of time depending on your internet connection. Monitor the container logs to see the progress.

4.  **Access the UI**: Once the server starts successfully (you'll see a Uvicorn message in the logs), open your web browser and go to:
    `http://localhost:8001`

5.  **Query the System**: Use the input box on the web page to ask a question related to the content of your PDF file. The system will process your query and display the answer along with the source pages.

## Deliverables Checklist

-   [x] **Code**: `main.py` contains the full RAG pipeline and FastAPI application. `Dockerfile` and `requirements.txt` are included.
-   [x] **REST API**: The endpoint `/query-api` handles POST requests with a JSON payload `{ "text": "your query" }`.
-   [x] **RAG endpoint demo via simple query page**: The root URL `/` provides a simple HTML interface for querying.
