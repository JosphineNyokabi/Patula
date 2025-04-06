# Technical Manual - Information Retrieval System
## Required Pre-Installed Software
Docker Desktop  
Visual Studio  
Github Desktop  
WSL - Ubuntu
## Component Breakdown  
1. Indexer - processes raw data and builds an index to make data retrievable 
2. Apache tika - extracts text, metadata, and language information from various file types
3. Elasticsearch - search and analytics engine, works alongside Kibana
4. Kibana- visualization and dashboard layer
## Step One
Save your corpus of documents in ubuntu - mnt - data for accessibility
## Step 2 - Create the Following Files/Folders in VS
### Docker Compose File
```
version: "3.9"
services:

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.6.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.6.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  tika:
    image: apache/tika
    ports:
      - "9998:9998"

  indexer:
    build: ./indexer
    volumes:
      - /mnt/data/pinecones:/mnt/data/pinecones
    depends_on:
      - tika
      - elasticsearch

volumes:
  esdata:
```
### Python Indexer
index.py
```
import os
import requests
import hashlib
from pathlib import Path


TIKA_SERVICE_URL = "http://tika:9998/tika"
ELASTICSEARCH_DOC_URL = "http://elasticsearch:9200/documents/_doc"
DOCUMENTS_DIR = Path("/mnt/data/pinecones")  


def compute_file_hash(file_path):
    """
    Generate a SHA-256 hash from the file's content.
    This hash is used as a consistent and unique document ID.
    """
    hash_obj = hashlib.sha256()
    with open(file_path, 'rb') as binary_file:
        for chunk in iter(lambda: binary_file.read(8192), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def extract_text_content(file_path):
    """
    Use Apache Tika to extract plain text content from a given file.
    Returns the text if successful, otherwise None.
    """
    try:
        with open(file_path, 'rb') as data:
            headers = {"Accept": "text/plain"}
            response = requests.put(
                TIKA_SERVICE_URL,
                data=data,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            return response.text
    except Exception as error:
        print(f"❌ Tika extraction failed for {file_path.name}: {error}")
        return None


def is_already_indexed(document_id):
    """
    Check Elasticsearch to see if the document has already been indexed.
    """
    response = requests.head(f"{ELASTICSEARCH_DOC_URL}/{document_id}")
    return response.status_code == 200


def index_document(document_id, file_path, content):
    """
    Send the document metadata and extracted content to Elasticsearch.
    """
    document_payload = {
        "filename": file_path.name,
        "path": str(file_path),
        "category": file_path.parent.name,
        "content": content
    }

    try:
        response = requests.put(
            f"{ELASTICSEARCH_DOC_URL}/{document_id}",
            json=document_payload
        )
        response.raise_for_status()
        print(f"✅ Indexed: {file_path}")
    except Exception as error:
        print(f"❌ Failed to index {file_path}: {error}")


def scan_and_index_documents():
    """
    Traverse the specified directory, extract text from files,
    and index them into Elasticsearch if they haven't been indexed already.
    """
    print(f"📁 Scanning directory: {DOCUMENTS_DIR}\n")

    for file_path in DOCUMENTS_DIR.rglob("*"):
        if not file_path.is_file():
            continue

        document_id = compute_file_hash(file_path)

        if is_already_indexed(document_id):
            print(f"⏭️ Skipped (already indexed): {file_path}")
            continue

        content = extract_text_content(file_path)
        if content:
            index_document(document_id, file_path, content)


if __name__ == "__main__":
    scan_and_index_documents()
```
### Docker File
```
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY index.py .

CMD ["python", "index.py"]
```
### requirements.txt
```
requests
```
### Step 3 Build the Docker Containers 
```
sudo docker-compose up -d
```
### Step 4 Run the Indexer
```
sudo docker-compose run indexer
```
### Step 5 Check if containers are running
```
sudo docker ps
```
## Access URLs
Kibana - http://localhost:5601  
Tika - http://localhost:9998  
Elasticsearch - http://localhost:9200
## Access Kibana
1. Visit- http://localhost:5601
2. Stackemanagent - Data Views - Name = Documents - (Skip time field)
3. Discover tab - explore documents (type key words in your documents)
## Visualizations
Select dashboards  
Select visualization of choice - bar charts, pie charts  

   
  ~ THE END ~


