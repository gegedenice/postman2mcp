import json
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Tuple

def extract_query_parameters(url_obj: Dict) -> List[Dict]:
    return [
        {
            "name": param["key"],
            "in": "query",
            "schema": {
                "type": infer_type_from_value(param.get("value", ""))
            },
            "description": param.get("description", "")
        }
        for param in url_obj.get("query", []) if param.get("key")
    ]
    
def infer_type_from_value(value: str) -> str:
    if not value:
        return "string"  # fallback default
    if value in ["true", "false"]:
        return "boolean"
    if value.isdigit():
        return "integer"
    try:
        float(value)
        return "number"
    except ValueError:
        return "string"


def extract_path(url_obj: Dict) -> str:
    segments = url_obj.get("path", [])
    if "{id}" in segments:
        return "/" + "/".join(segments)
    return "/" + "/".join(segments)

def extract_examples(responses: List[Dict]) -> Dict:
    examples = {}
    for i, resp in enumerate(responses):
        req = resp.get("originalRequest", {})
        url_obj = req.get("url", {})
        query_list = url_obj.get("query", [])
        query_dict = {
            param["key"]: param.get("value", "")
            for param in query_list if param.get("key")
        }
        summary = resp.get("name", f"example_{i+1}")
        examples[f"example_{i+1}"] = {
            "summary": summary,
            "value": query_dict
        }
    return examples

def extract_base_url_from_first_request(items: List[Dict]) -> str:
    """
    Recursively traverse items to find the first request and extract its base URL.
    """
    for item in items:
        if "item" in item:
            # Folder, recurse
            url = extract_base_url_from_first_request(item["item"])
            if url:
                return url
        else:
            request = item.get("request", {})
            url_obj = request.get("url", {})
            # Prefer 'raw' if available, else reconstruct from protocol/host
            if "raw" in url_obj:
                raw_url = url_obj["raw"]
                parsed = urlparse(raw_url)
                return f"{parsed.scheme}://{parsed.netloc}"
            elif "protocol" in url_obj and "host" in url_obj:
                protocol = url_obj["protocol"]
                host = url_obj["host"]
                if isinstance(host, list):
                    host = ".".join(host)
                return f"{protocol}://{host}"
    return "http://localhost:8000"  # fallback

def convert_to_openapi(postman_collection) -> Tuple[dict, str]:
    postman = postman_collection if isinstance(postman_collection, dict) else json.loads(postman_collection)
    openapi = {
        "openapi": "3.1.0",
        "info": {
            "title": postman["collection"]["info"]["name"],
            "version": "1.0.0",
            "description": postman["collection"]["info"]["description"]
        },
        "paths": {}
    }

    def process_items(items: List[Dict]):
        for item in items:
            if "item" in item:
                process_items(item["item"])  # Recurse into folders
            else:
                request = item.get("request", {})
                if not request:
                    continue

                method = request.get("method", "GET").lower()
                url_obj = request.get("url", {})
                path = extract_path(url_obj)
                parameters = extract_query_parameters(url_obj)
                summary = item.get("name", f"{method.upper()} {path}")
                description = request.get("description", "")

                examples = extract_examples(item.get("response", []))

                if path not in openapi["paths"]:
                    openapi["paths"][path] = {}
                openapi["paths"][path][method] = {
                    "summary": summary,
                    "description": description,
                    "parameters": parameters,
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "examples": examples or {
                                        "default_example": {
                                            "summary": summary,
                                            "value": {}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
    def reinject_examples_in_description(openapi):
        for path, methods in openapi.get("paths", {}).items():
            for method, details in methods.items():
                desc = details.get("description", "")
                responses = details.get("responses", {})
                for resp in responses.values():
                    content = resp.get("content", {})
                    for ctype in content.values():
                        examples = ctype.get("examples", {})
                        if examples:
                            desc += "\n\n---\n**Examples:**\n"
                            for ex in examples.values():
                                desc += f"- {ex.get('summary', '')}: `{ex.get('value', '')}`\n"
                details["description"] = desc
        return openapi

    process_items(postman["collection"]["item"])
    base_url = extract_base_url_from_first_request(postman["collection"]["item"])
    openapi["servers"] = [{"url": "http://localhost:8000"}]
    openapi = reinject_examples_in_description(openapi)
    return openapi,base_url