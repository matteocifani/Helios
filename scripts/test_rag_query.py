
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.db_utils import get_supabase_client

load_dotenv()

def test_rag():
    print("Testing RAG for client 9501...")
    
    # 1. Setup
    client = get_supabase_client()
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not client or not api_key:
        print("❌ Missing credentials")
        return

    query = "Ci sono stati problemi recenti?"
    client_id = 9501

    # 2. Generate Embedding
    print("Generating embedding...")
    try:
        emb_response = requests.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/text-embedding-3-small",
                "input": query
            },
            timeout=10
        )
        embedding = emb_response.json()["data"][0]["embedding"]
        print("✅ Embedding generated")
    except Exception as e:
        print(f"❌ Embedding failed: {e}")
        return

    # 3. Call RPC
    print("Calling match_interactions RPC...")
    try:
        response = client.rpc(
            "match_interactions",
            {
                "query_embedding": embedding,
                "match_threshold": 0.1,  # Lowered for testing
                "match_count": 5,
                "filter_client_id": client_id
            }
        ).execute()
        
        results = response.data
        print(f"✅ RPC Success. Found {len(results)} matches.")
        
        for i, res in enumerate(results):
            print(f"\n--- Match {i+1} (Similarity: {res['similarity']:.4f}) ---")
            print(f"Date: {res['data_interazione']}")
            print(f"Type: {res['tipo_interazione']}")
            print(f"Outcome: {res['esito']}")
            print(f"Note: {res['note']}")
            
    except Exception as e:
        print(f"❌ RPC Failed: {e}")

if __name__ == "__main__":
    test_rag()
