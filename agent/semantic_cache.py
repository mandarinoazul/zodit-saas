import httpx
import json
import asyncio
import os
import math
from typing import Optional, Dict, Any, List
from config import BASE_DIR
from logger import log

CACHE_FILE = os.path.join(BASE_DIR, "assets", "semantic_cache.json")
EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
SIMILARITY_THRESHOLD = 0.90

# In-memory cache store
# Structure: [ {"prompt": "...", "vector": [...], "response": "..."}, ... ]
_memory_cache: List[Dict[str, Any]] = []


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate the cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


async def get_embedding(text: str) -> Optional[List[float]]:
    """Fetch the vector embedding for a given text from Ollama asynchronously."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            payload = {"model": EMBEDDING_MODEL, "prompt": text}
            resp = await client.post(OLLAMA_EMBED_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding")
            else:
                log.warning(f"Embedding failed with HTTP {resp.status_code}")
                return None
    except Exception as e:
        log.error(f"Error fetching embedding: {e}")
        return None

def load_cache():
    """Load the cache from disk."""
    global _memory_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _memory_cache = json.load(f)
            log.info(f"[CACHE] Loaded {len(_memory_cache)} elements from disk.")
        except Exception as e:
            log.error(f"[CACHE] Error loading file: {e}")
            _memory_cache = []

def save_cache():
    """Save the in-memory cache to disk."""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_cache, f, indent=4)
    except Exception as e:
        log.error(f"[CACHE] Error saving file: {e}")

async def check_cache(prompt: str) -> Optional[str]:
    """
    Check if a similar prompt exists in the cache.
    Returns the cached response if similarity > SIMILARITY_THRESHOLD, else None.
    """
    if not _memory_cache:
        return None
        
    vec = await get_embedding(prompt)
    if not vec:
        return None
        
    best_match = None
    best_score = -1.0
    
    for item in _memory_cache:
        cached_vec = item.get("vector")
        if not cached_vec:
            continue
            
        score = _cosine_similarity(vec, cached_vec)
        if score > best_score:
            best_score = score
            best_match = item
            
    if best_match and best_score >= SIMILARITY_THRESHOLD:
        log.info(f"[CACHE HIT] Similarity: {best_score:.4f} for prompt: {prompt[:30]}...")
        return best_match.get("response")
        
    log.debug(f"[CACHE MISS] Best similarity: {best_score:.4f}")
    return None

async def store_in_cache(prompt: str, response: str):
    """Embed the prompt and store the prompt-response pair in the cache."""
    vec = await get_embedding(prompt)
    if not vec:
        return
        
    _memory_cache.append({
        "prompt": prompt,
        "vector": vec,
        "response": response
    })
    
    # Save asynchronously so we don't block
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, save_cache)
    log.info(f"[CACHE STORED] Added to cache: {prompt[:30]}...")

# Initial Load
load_cache()
