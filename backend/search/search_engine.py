import re
import json
from typing import List, Dict, Any
from ..engine.dependency_graph import categorize_endpoint

class ContextualSearchEngine:
    """
    Contextual, multi-field API search engine.
    Matches across URL endpoints, titles, body payloads, headers, chained variables, and lifecycle contexts.
    """

    @classmethod
    def search(cls, requests: List[Dict[str, Any]], collections: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        query = (query or "").strip().lower()
        if not query:
            # Return all requests categorized
            results = []
            col_map = {c["id"]: c["name"] for c in collections}
            for req in requests:
                cat = categorize_endpoint(req)
                results.append({
                    "id": req["id"],
                    "collection_id": req.get("collection_id"),
                    "collection_name": col_map.get(req.get("collection_id"), "Default"),
                    "name": req.get("name") or req.get("url", ""),
                    "method": (req.get("method") or "GET").upper(),
                    "url": req.get("url", ""),
                    "category": cat,
                    "match_type": "all",
                    "snippet": req.get("url", ""),
                    "score": 0,
                    "body_type": req.get("body_type", "json"),
                    "extracts": req.get("extracts_json") or []
                })
            return results

        tokens = [t for t in re.split(r'\s+', query) if t]
        col_map = {c["id"]: c["name"] for c in collections}
        scored_results = []

        for req in requests:
            req_id = req["id"]
            name = (req.get("name") or "").lower()
            url = (req.get("url") or "").lower()
            method = (req.get("method") or "GET").upper()
            body = (req.get("body") or "").lower()
            
            headers_raw = req.get("headers_json") or "{}"
            if isinstance(headers_raw, dict):
                headers_str = json.dumps(headers_raw).lower()
            else:
                headers_str = str(headers_raw).lower()

            extracts_raw = req.get("extracts_json") or []
            if isinstance(extracts_raw, list):
                extracts_str = json.dumps(extracts_raw).lower()
            else:
                extracts_str = str(extracts_raw).lower()

            col_name = col_map.get(req.get("collection_id"), "").lower()
            category = categorize_endpoint(req)
            category_lower = category.lower()

            score = 0
            match_reasons = []
            snippet = ""

            # Check full query match
            if query == url or query in url:
                score += 50
                match_reasons.append("Endpoint URL")
                snippet = f"URL: {req.get('url')}"

            if query in name:
                score += 40
                match_reasons.append("API Name")
                if not snippet: snippet = f"Title: {req.get('name')}"

            if query == method.lower():
                score += 30
                match_reasons.append("HTTP Method")

            if query in category_lower:
                score += 25
                match_reasons.append(f"Room: {category}")

            if query in extracts_str:
                score += 35
                match_reasons.append("Chained Variables")
                if not snippet: snippet = f"Extracts: {extracts_str[:80]}"

            if query in body:
                score += 30
                match_reasons.append("Request Payload")
                # Extract surrounding context snippet
                idx = body.find(query)
                start = max(0, idx - 20)
                end = min(len(body), idx + len(query) + 40)
                if not snippet:
                    snippet = f"...{body[start:end].replace(chr(10), ' ')}..."

            if query in headers_str:
                score += 20
                match_reasons.append("Headers")

            if query in col_name:
                score += 15
                match_reasons.append(f"Collection: {col_map.get(req.get('collection_id'))}")

            # Also check multi-token matching
            for token in tokens:
                if token in url: score += 15
                if token in name: score += 12
                if token in body: score += 8
                if token in extracts_str: score += 10
                if token in category_lower: score += 8

            if score > 0:
                scored_results.append({
                    "id": req_id,
                    "collection_id": req.get("collection_id"),
                    "collection_name": col_map.get(req.get("collection_id"), "Default"),
                    "name": req.get("name") or req.get("url", ""),
                    "method": method,
                    "url": req.get("url", ""),
                    "category": category,
                    "match_type": ", ".join(match_reasons) if match_reasons else "Keyword",
                    "snippet": snippet or req.get("url", ""),
                    "score": score,
                    "body_type": req.get("body_type", "json"),
                    "extracts": req.get("extracts_json") or []
                })

        # Sort descending by relevance score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results
