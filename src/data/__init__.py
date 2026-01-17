"""Data access module for Helios."""
from .db_utils import (
    get_supabase_client,
    fetch_abitazioni,
    fetch_clienti,
    check_client_interactions,
    is_client_eligible_for_top20,
    check_all_clients_interactions_batch,
    insert_phone_call_interaction,
    search_clients,
)
