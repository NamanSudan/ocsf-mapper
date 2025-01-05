```markdown:trieve_integration_guide.md
# Trieve Integration with a Python Flask App

This document provides end-to-end instructions on how to integrate the Trieve API into a Python Flask web application. We will cover:

1. Installing and configuring the Python SDK.  
2. Setting up environment variables (API key, dataset ID, etc.).  
3. Creating a minimal Flask application with endpoints to interact with Trieve.  
4. Demonstrating common use cases: chunk creation, querying, RAG usage, etc.

---

## 1. Prerequisites

• A Python environment (3.8+ recommended).  
• Flask installed (or install via pip: `pip install flask`).  
• Trieve API credentials (API key, dataset ID, organization ID if you have one).  
• (Optional) Docker or Docker Compose if you plan to containerize.  

---

## 2. Installing the Trieve Python SDK

To integrate with Trieve from Python, you can use the “trieve-py-client” library published on PyPI. Install it with:

```bash
pip install trieve-py-client
```

---

## 3. Basic Folder Structure

Below is a suggested structure for your Flask application:

```
my-flask-app/
├── app.py
├── requirements.txt
├── .env
└── ...
```

Where:
• `app.py` is your Flask entry point.  
• `.env` holds environment variables such as `TRIEVE_API_KEY`, `TRIEVE_DATASET_ID`, etc.

Example `.env` file:

```
TRIEVE_API_KEY=tr-********************************
TRIEVE_DATASET_ID=********-****-****-****-************
TRIEVE_ORGANIZATION_ID=********-****-****-****-************
```

(Ensure you do not commit real secrets in version control.)

---

## 4. Configuring the Python SDK

In your Flask application, you will configure the Trieve client. For example:

```python
# app.py
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from trieve_py_client.api import chunk_api
from trieve_py_client.configuration import Configuration
from trieve_py_client import ApiClient

load_dotenv()

app = Flask(__name__)

# Read environment variables
TRIEVE_API_KEY = os.getenv("TRIEVE_API_KEY")
TRIEVE_DATASET_ID = os.getenv("TRIEVE_DATASET_ID")

# Configure the Trieve client
config = Configuration(
    host="https://api.trieve.ai",  # or your self-hosted instance
    api_key={
        "Authorization": TRIEVE_API_KEY,
    },
    # Optional additional config settings here
)

# Instantiate the client and relevant endpoints
trieve_client = ApiClient(config)
chunk_endpoint = chunk_api.ChunkApi(trieve_client)
```

Notes:  
• We’re using `dotenv` to load env variables from `.env`.  
• The `ChunkApi` class can handle chunk-related operations such as creating, updating, searching, etc.  

---

## 5. Example: Creating a Chunk

You can create (or upsert) a chunk to store data in Trieve. In your Flask routes:

```python
@app.route("/create-chunk", methods=["POST"])
def create_chunk():
    # Example JSON payload from client:
    # {
    #   "content": "Some text about AI expansion",
    #   "metadata": {"source": "internal-docs"},
    #   "tags": ["ai", "expansion"]
    # }

    req_data = request.get_json(force=True)
    content = req_data.get("content")
    metadata = req_data.get("metadata", {})
    tags = req_data.get("tags", [])

    create_chunk_payload = {
        "content": content, 
        "metadata": metadata, 
        "tags": tags
    }

    try:
        result = chunk_endpoint.create_or_upsert_chunk(
            dataset_id=TRIEVE_DATASET_ID,
            create_or_upsert_chunk_req_payload=[create_chunk_payload]  # list of chunks
        )
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
```

Explanation:  
• The `create_or_upsert_chunk` method accepts a list of chunk objects. Each chunk must have `content`.  
• Optionally, you can include `metadata`, `tags`, etc., to help filter or retrieve chunks later.  

---

## 6. Example: Searching for Chunks

You can perform both semantic or hybrid searches. Below is a simple search endpoint that uses “search_type” to pick the method:

```python
@app.route("/search-chunks", methods=["POST"])
def search_chunks():
    # Example JSON payload from client:
    # {
    #   "query": "What is the future of AI?",
    #   "search_type": "hybrid"
    # }

    req_data = request.get_json(force=True)
    query = req_data.get("query", "")
    search_type = req_data.get("search_type", "semantic")

    search_payload = {
        "query": query,
        "search_type": search_type,
        "limit": 5  # number of results
    }

    try:
        results = chunk_endpoint.search_chunks(
            dataset_id=TRIEVE_DATASET_ID,
            search_chunk_req_payload=search_payload
        )
        return jsonify({"status": "success", "data": results.to_dict()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
```

Here, the `search_type` can be “semantic”, “bm25”, “splade”, or “hybrid”. You can also pass additional fields like `score_threshold`, filters, etc.

---

## 7. Example: RAG Usage

Trieve supports retrieval-augmented generation (RAG). From the code snippet reference in the repository (like “rag.py”), you can store or retrieve RAG events. A typical RAG flow is:

1. Search for relevant chunks.  
2. Send top chunks as context to an LLM.  
3. Store the LLM’s response back to Trieve as a “rag” event (helpful for analytics or re-query).

For a minimal example of storing a RAG event:

```python
from trieve_py_client.models.rag import RAG

@app.route("/store-rag", methods=["POST"])
def store_rag():
    # Example payload: 
    # {
    #   "llm_response": "AI is predicted to shape many industries...",
    #   "user_message": "Summarize the future of AI"
    # }

    req_data = request.get_json(force=True)
    user_message = req_data["user_message"]
    llm_response = req_data["llm_response"]

    # RAG objects typically have an event_type of "rag"
    rag_event = RAG(
        event_type="rag",
        user_message=user_message,
        llm_response=llm_response
    )
    # You would forward this to an endpoint for analytics or logging.
    # E.g., chunk_endpoint.log_rag_event(...) if the API exposes it.
    # Or store in your custom db or Trieve's analytics endpoint.

    return jsonify({"status": "RAG event created"}), 200
```

(This code is illustrative only; check the actual endpoints in your Python SDK or the OpenAPI docs to see which method handles RAG events.)

---

## 8. Putting It All Together: Minimal Flask App

Below is a simplified `app.py` that shows the typical usage flows:

```python
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

from trieve_py_client.configuration import Configuration
from trieve_py_client.api_client import ApiClient
from trieve_py_client.api import chunk_api

load_dotenv()

app = Flask(__name__)

# Environment variables
TRIEVE_API_KEY = os.getenv("TRIEVE_API_KEY")
TRIEVE_DATASET_ID = os.getenv("TRIEVE_DATASET_ID")
TRIEVE_HOST = os.getenv("TRIEVE_HOST", "https://api.trieve.ai")

# Configure Trieve
config = Configuration(
    host=TRIEVE_HOST,
    api_key={"Authorization": TRIEVE_API_KEY}
)
trieve_client = ApiClient(config)
chunk_endpoint = chunk_api.ChunkApi(trieve_client)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/create-chunk", methods=["POST"])
def create_chunk():
    data = request.get_json(force=True)
    chunk_payload = {
        "content": data.get("content"),
        "metadata": data.get("metadata", {}),
        "tags": data.get("tags", [])
    }

    try:
        result = chunk_endpoint.create_or_upsert_chunk(
            dataset_id=TRIEVE_DATASET_ID,
            create_or_upsert_chunk_req_payload=[chunk_payload]
        )
        return jsonify({"success": True, "data": result.to_dict()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/search-chunks", methods=["POST"])
def search_chunks():
    data = request.get_json(force=True)
    search_payload = {
        "query": data.get("query", ""),
        "search_type": data.get("search_type", "semantic"),
        "limit": 5
    }
    try:
        results = chunk_endpoint.search_chunks(
            dataset_id=TRIEVE_DATASET_ID,
            search_chunk_req_payload=search_payload
        )
        return jsonify({"success": True, "data": results.to_dict()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
```

You can run this app locally with:
```bash
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5000
```
Or simply:
```bash
python app.py
```
Then test with a tool like `curl`:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"Hello world"}' \
  http://localhost:5000/create-chunk
```

---

## 9. Troubleshooting & Tips

1. **Authentication Issues**: Check if you are sending the correct API key and dataset ID.  
2. **Dataset Not Found**: Ensure you have created a dataset in the Trieve console or via an admin route.  
3. **Search Type**: If your logs are not returning results, try “hybrid” or “splade” for better coverage.  
4. **Large Files**: If chunking large files, consider batch upserts and watch for request size limits.

---

## 10. Next Steps

• Explore additional endpoints (e.g., uploading files, group-level operations).  
• Incorporate RAG endpoints if you want to store LLM events or analytics.  
• Optionally integrate a cross-encoder re-ranker for more precise search results.  
• Use the advanced filtering or date-range queries if your data demands it.

---

## 11. References

• Trieve Python SDK:  
  – Documentation: [PyPI: trieve-py-client](https://pypi.org/project/trieve-py-client/)  
  – Example classes: “rag.py” and the “chunk_api.py” in the codebase.  
• Official Trieve Documentation: [docs.trieve.ai](https://docs.trieve.ai)  
• Flask Documentation: [Flask.palletsprojects.com](https://flask.palletsprojects.com/)  

---

*This concludes the detailed integration guide for building a Python Flask app using Trieve.*  
```
