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
