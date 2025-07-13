import os
import chromadb
import requests
import chromadb.utils.embedding_functions as embedding_functions

def list_to_string(lst, max_length=100):
    if isinstance(lst, list):
        result = ", ".join(map(str, lst))
        if len(result) > max_length:
            return result[:max_length] + "..."
        return result
    return lst

def sanitize_metadata(metadata):
    if isinstance(metadata.get('brand'), list):
        metadata['brand'] = ", ".join(map(str, metadata['brand']))
    if isinstance(metadata.get('tags'), list):
        metadata['tags'] = list_to_string(metadata['tags'], max_length=50)
    if isinstance(metadata.get('reviews'), list):
        metadata['reviews'] = list_to_string([review['comment'] for review in metadata.get('reviews', [])], max_length=100)
    if isinstance(metadata.get('images'), list):
        metadata['images'] = list_to_string(metadata['images'], max_length=100)
    if metadata.get('brand') is None:
        metadata['brand'] = "Unknown Brand"
    return metadata

def get_chroma_collection():
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CHROMA_API_KEY = os.getenv('CHROMA_API_KEY')
    CHROMA_TENANT = os.getenv('CHROMA_TENANT')
    CHROMA_DATABASE = os.getenv('CHROMA_DATABASE')
    if not all([GEMINI_API_KEY, CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE]):
        raise EnvironmentError("Missing one or more required environment variables: GEMINI_API_KEY, CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE")
    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=GEMINI_API_KEY)
    client = chromadb.CloudClient(
        api_key=CHROMA_API_KEY,
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE
    )
    try:
        client.delete_collection("dev_collection")
    except Exception:
        pass
    collection = client.get_or_create_collection("dev_collection", embedding_function=google_ef)
    return collection

def add_products_to_collection(collection):
    resp = requests.get("https://dummyjson.com/products?limit=0")
    resp.raise_for_status()
    data = resp.json()
    products = data.get("products", [])
    documents = []
    metadatas = []
    ids = []
    for prod in products:
        doc = f"{prod.get('title', '')} - {prod.get('description', '')}"
        documents.append(doc)
        tags_str = list_to_string(prod.get("tags", []), max_length=50)
        reviews_str = list_to_string([review['comment'] for review in prod.get("reviews", [])], max_length=100)
        images = prod.get("images", [])
        image = images[0] if images else ""
        metadata = {
            "id": prod.get("id"),
            "title": prod.get("title"),
            "category": prod.get("category"),
            "price": prod.get("price"),
            "brand": prod.get("brand"),
            "tags": tags_str,
            "rating": prod.get("rating"),
            "reviews": reviews_str,
            "images": image,
            "availability": prod.get("availabilityStatus"),
            "warranty": prod.get("warrantyInformation")
        }
        sanitized_metadata = sanitize_metadata(metadata)
        metadatas.append(sanitized_metadata)
        ids.append(f"prod_{prod.get('id')}")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

def query_collection(collection, query_text="dress", n_results=5):
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    collection = get_chroma_collection()
    add_products_to_collection(collection)
    results = query_collection(collection, query_text="dress", n_results=5)
    print(results) 