import requests

def harvest_postman_collection(collection_id, postman_api_key):
    url = f"https://api.postman.com/collections/{collection_id}"
    headers = {
        "X-Api-Key": postman_api_key
    }
    print(f"Fetching collection from {url}...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch collection: {response.status_code} {response.text}")
    print(f"Collection ID: {collection_id} fetched successfully!")
    return response.json()