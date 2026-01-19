
import os
import sys
# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.db_utils import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

def check_embeddings():
    client = get_supabase_client()
    if not client:
        print("No client")
        return

    try:
        # Count total rows
        count_res = client.table("interactions").select("id", count="exact").execute()
        total = count_res.count
        
        # Count rows with embedding
        embed_res = client.table("interactions").select("id", count="exact").not_.is_("embedding", "null").execute()
        with_embed = embed_res.count
        
        print(f"Total interactions: {total}")
        print(f"Interactions with embedding: {with_embed}")
        
        if with_embed > 0:
            # Check one to see if it looks right
            sample = client.table("interactions").select("embedding").not_.is_("embedding", "null").limit(1).execute()
            emb_val = sample.data[0]['embedding']
            print(f"Sample embedding type: {type(emb_val)}")
            if isinstance(emb_val, str):
                print(f"Sample embedding (first 50 chars): {emb_val[:50]}...")
            elif isinstance(emb_val, list):
                 print(f"Sample embedding length: {len(emb_val)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_embeddings()
