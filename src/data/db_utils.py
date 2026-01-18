"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    HELIOS DATABASE UTILITIES                                   ║
║              Supabase Connection & Data Access Layer                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Import constants
from src.config.constants import (
    DB_CHUNK_SIZE,
    DB_MAX_SEARCH_RESULTS,
    CACHE_TTL_SHORT,
    CACHE_TTL_MEDIUM,
    API_MAX_RETRIES,
    API_RETRY_DELAY_SECONDS,
    ABITAZIONI_COLUMNS,
    CLIENTI_COLUMNS,
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseConnectionError(Exception):
    """Custom exception for Supabase connection failures."""
    pass


class SupabaseQueryError(Exception):
    """Custom exception for Supabase query failures."""
    pass


@st.cache_resource
def get_supabase_client() -> Optional[Client]:
    """
    Initialize and cache Supabase client connection with proper error handling.

    Returns:
        Supabase Client instance or None if connection fails

    Raises:
        SupabaseConnectionError: If credentials are missing or connection fails
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    # Validate credentials
    if not url or not key:
        error_msg = "⚠️ Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env file."
        logger.error(error_msg)
        st.error(error_msg)
        return None

    if not url.startswith("http"):
        error_msg = f"⚠️ Invalid SUPABASE_URL format: {url}"
        logger.error(error_msg)
        st.error(error_msg)
        return None

    try:
        client = create_client(url, key)
        logger.info("✅ Supabase client initialized successfully")
        return client
    except Exception as e:
        error_msg = f"⚠️ Failed to initialize Supabase client: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return None


def _retry_query(func, *args, **kwargs):
    """
    Retry a database query with exponential backoff.

    Args:
        func: Function to retry
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func if successful

    Raises:
        SupabaseQueryError: If all retries fail
    """
    for attempt in range(API_MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == API_MAX_RETRIES - 1:
                raise SupabaseQueryError(f"Query failed after {API_MAX_RETRIES} attempts: {str(e)}")

            wait_time = API_RETRY_DELAY_SECONDS * (2 ** attempt)
            logger.warning(f"Query attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time}s...")
            time.sleep(wait_time)


@st.cache_data(ttl=CACHE_TTL_SHORT)
def fetch_abitazioni() -> pd.DataFrame:
    """
    Fetch all abitazioni with risk scores from Supabase using chunked pagination.

    Returns:
        DataFrame with abitazioni data or empty DataFrame with expected columns
    """
    client = get_supabase_client()
    if not client:
        logger.warning("No Supabase client available, returning empty DataFrame")
        return pd.DataFrame(columns=ABITAZIONI_COLUMNS)

    try:
        all_data = []
        offset = 0

        while True:
            try:
                response = _retry_query(
                    lambda: client.table("abitazioni").select(
                        "id, codice_cliente, citta, latitudine, longitudine, "
                        "zona_sismica, hydro_risk_p3, hydro_risk_p2, flood_risk_p4, flood_risk_p3, "
                        "risk_score, risk_category, solar_potential_kwh, updated_at"
                    ).range(offset, offset + DB_CHUNK_SIZE - 1).execute()
                )

                data = response.data
                if not data or len(data) == 0:
                    break

                all_data.extend(data)
                logger.info(f"Fetched {len(data)} abitazioni records (offset: {offset})")

                if len(data) < DB_CHUNK_SIZE:
                    break

                offset += DB_CHUNK_SIZE

            except SupabaseQueryError as e:
                logger.error(f"Error fetching abitazioni chunk at offset {offset}: {e}")
                break

        if not all_data:
            logger.warning("No abitazioni data retrieved")
            return pd.DataFrame(columns=ABITAZIONI_COLUMNS)

        df = pd.DataFrame(all_data)
        logger.info(f"Successfully fetched {len(df)} total abitazioni records")
        return df

    except Exception as e:
        logger.error(f"Unexpected error in fetch_abitazioni: {e}")
        st.error(f"Error fetching abitazioni: {e}")
        return pd.DataFrame(columns=ABITAZIONI_COLUMNS)


@st.cache_data(ttl=CACHE_TTL_SHORT)
def fetch_clienti() -> pd.DataFrame:
    """
    Fetch client data with CLV and churn probability using chunked pagination.

    Returns:
        DataFrame with client data or empty DataFrame with expected columns
    """
    client = get_supabase_client()
    if not client:
        logger.warning("No Supabase client available, returning empty DataFrame")
        return pd.DataFrame(columns=CLIENTI_COLUMNS)

    try:
        all_data = []
        offset = 0

        while True:
            try:
                response = _retry_query(
                    lambda: client.table("clienti").select(
                        "codice_cliente, nome, cognome, eta, professione, reddito, "
                        "churn_probability, clv_stimato, latitudine, longitudine, num_polizze"
                    ).range(offset, offset + DB_CHUNK_SIZE - 1).execute()
                )

                data = response.data
                if not data or len(data) == 0:
                    break

                all_data.extend(data)
                logger.info(f"Fetched {len(data)} client records (offset: {offset})")

                if len(data) < DB_CHUNK_SIZE:
                    break

                offset += DB_CHUNK_SIZE

            except SupabaseQueryError as e:
                logger.error(f"Error fetching clienti chunk at offset {offset}: {e}")
                break

        if not all_data:
            logger.warning("No client data retrieved")
            return pd.DataFrame(columns=CLIENTI_COLUMNS)

        df = pd.DataFrame(all_data)
        logger.info(f"Successfully fetched {len(df)} total client records")
        return df

    except Exception as e:
        logger.error(f"Unexpected error in fetch_clienti: {e}")
        st.error(f"Error fetching clienti: {e}")
        return pd.DataFrame(columns=CLIENTI_COLUMNS)


@st.cache_data(ttl=CACHE_TTL_SHORT)
def fetch_risk_stats() -> Dict:
    """
    Fetch aggregated risk statistics with improved fallback logic.

    Returns:
        Dictionary with risk distribution statistics
    """
    client = get_supabase_client()
    if not client:
        return _get_empty_risk_stats()

    try:
        # Try RPC function first
        response = _retry_query(
            lambda: client.rpc("get_risk_distribution").execute()
        )

        if response.data and len(response.data) > 0:
            logger.info("Risk stats fetched via RPC")
            return response.data

    except SupabaseQueryError as e:
        logger.warning(f"RPC get_risk_distribution failed: {e}")

    # Fallback: calculate from cached data (separate cache key)
    return _calculate_risk_stats_fallback()


@st.cache_data(ttl=CACHE_TTL_SHORT)
def _calculate_risk_stats_fallback() -> Dict:
    """
    Fallback function to calculate risk stats from abitazioni data.
    Uses separate cache to avoid re-fetching if RPC fails repeatedly.

    Returns:
        Dictionary with risk statistics
    """
    try:
        df = fetch_abitazioni()
        if df.empty:
            return _get_empty_risk_stats()

        stats = df['risk_category'].value_counts().to_dict()
        result = {
            'critico': int(stats.get('Critico', 0)),
            'alto': int(stats.get('Alto', 0)),
            'medio': int(stats.get('Medio', 0)),
            'basso': int(stats.get('Basso', 0)),
            'total': len(df),
            'avg_score': round(float(df['risk_score'].mean()), 1) if 'risk_score' in df.columns else 0
        }
        logger.info("Risk stats calculated via fallback")
        return result
    except Exception as e:
        logger.error(f"Fallback risk stats calculation failed: {e}")
        return _get_empty_risk_stats()


def _get_empty_risk_stats() -> Dict:
    """Return empty risk stats structure."""
    return {
        'critico': 0,
        'alto': 0,
        'medio': 0,
        'basso': 0,
        'total': 0,
        'avg_score': 0
    }


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def fetch_seismic_zones() -> pd.DataFrame:
    """
    Fetch reference seismic zone data (longer cache for static reference data).

    Returns:
        DataFrame with seismic zone reference data
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()

    try:
        response = _retry_query(
            lambda: client.table("ref_seismic_zones").select("*").execute()
        )
        df = pd.DataFrame(response.data)
        logger.info(f"Fetched {len(df)} seismic zone records")
        return df
    except Exception as e:
        logger.error(f"Error fetching seismic zones: {e}")
        st.error(f"Error fetching seismic zones: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL_MEDIUM)
def fetch_hydro_zones() -> pd.DataFrame:
    """
    Fetch reference hydrogeological risk data (longer cache for static reference data).

    Returns:
        DataFrame with hydrogeological zone reference data
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()

    try:
        response = _retry_query(
            lambda: client.table("ref_hydrogeological_zones").select("*").execute()
        )
        df = pd.DataFrame(response.data)
        logger.info(f"Fetched {len(df)} hydro zone records")
        return df
    except Exception as e:
        logger.error(f"Error fetching hydro zones: {e}")
        st.error(f"Error fetching hydro zones: {e}")
        return pd.DataFrame()


def get_client_detail(codice_cliente: int) -> Dict:
    """
    Get detailed information for a specific client using concurrent requests
    to solve N+1 query problem.

    Args:
        codice_cliente: Client ID to fetch details for

    Returns:
        Dictionary with client, abitazioni, polizze, and sinistri data
    """
    client = get_supabase_client()
    if not client:
        return {"error": "Database connection not available"}

    def fetch_client_info():
        """Fetch client basic info."""
        try:
            response = _retry_query(
                lambda: client.table("clienti").select("*").eq("codice_cliente", codice_cliente).single().execute()
            )
            return ("cliente", response.data if response.data else {})
        except Exception as e:
            logger.error(f"Error fetching client info: {e}")
            return ("cliente", {})

    def fetch_abitazioni_info():
        """Fetch client properties."""
        try:
            response = _retry_query(
                lambda: client.table("abitazioni").select("*").eq("codice_cliente", codice_cliente).execute()
            )
            return ("abitazioni", response.data if response.data else [])
        except Exception as e:
            logger.error(f"Error fetching abitazioni info: {e}")
            return ("abitazioni", [])

    def fetch_polizze_info():
        """Fetch client policies."""
        try:
            response = _retry_query(
                lambda: client.table("polizze").select("*").eq("codice_cliente", codice_cliente).execute()
            )
            return ("polizze", response.data if response.data else [])
        except Exception as e:
            logger.error(f"Error fetching polizze info: {e}")
            return ("polizze", [])

    def fetch_sinistri_info():
        """Fetch client claims."""
        try:
            response = _retry_query(
                lambda: client.table("sinistri").select("*").eq("codice_cliente", codice_cliente).execute()
            )
            return ("sinistri", response.data if response.data else [])
        except Exception as e:
            logger.error(f"Error fetching sinistri info: {e}")
            return ("sinistri", [])

    # Execute all queries concurrently
    result = {}
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(fetch_client_info),
                executor.submit(fetch_abitazioni_info),
                executor.submit(fetch_polizze_info),
                executor.submit(fetch_sinistri_info)
            ]

            for future in as_completed(futures):
                try:
                    key, data = future.result()
                    result[key] = data
                except Exception as e:
                    logger.error(f"Error in concurrent query: {e}")

        logger.info(f"Fetched complete details for client {codice_cliente}")
        return result

    except Exception as e:
        logger.error(f"Error fetching client detail: {e}")
        st.error(f"Error fetching client detail: {e}")
        return {"error": str(e)}


@st.cache_data(ttl=60)
def search_clients(query: str, limit: int = DB_MAX_SEARCH_RESULTS) -> pd.DataFrame:
    """
    Search clients by ID, name, or city with proper parameterization.
    Cached for 60 seconds to avoid repeated queries for same search.

    Args:
        query: Search query string
        limit: Maximum number of results to return

    Returns:
        DataFrame with search results
    """
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()

    if not query or len(query.strip()) == 0:
        return pd.DataFrame()

    # Sanitize input
    query = query.strip()

    try:
        # Use ilike for case-insensitive search (Supabase handles sanitization)
        response = _retry_query(
            lambda: client.table("abitazioni").select(
                "*, clienti(nome, cognome, churn_probability)"
            ).or_(
                f"id.ilike.%{query}%,"
                f"codice_cliente.ilike.%{query}%,"
                f"citta.ilike.%{query}%"
            ).limit(limit).execute()
        )

        df = pd.DataFrame(response.data)
        logger.info(f"Search for '{query}' returned {len(df)} results")
        return df

    except Exception as e:
        logger.error(f"Error searching clients: {e}")
        st.error(f"Error searching clients: {e}")
        return pd.DataFrame()


def check_client_interactions(codice_cliente: str) -> Dict[str, bool]:
    """
    Check client interaction indicators for filtering Top 20 clients.

    A client should NOT appear in Top 20 if any indicator is True.

    Args:
        codice_cliente: Client ID to check (can be string like "CLI_9500" or integer)

    Returns:
        Dictionary with boolean indicators:
        - email_last_5_days: Email sent in last 5 business days
        - call_last_10_days: Phone call in last 10 days
        - new_policy_last_30_days: New policy issued in last 30 days
        - open_complaint: Has open complaint
        - claim_last_60_days: Claim in last 60 days
    """
    from datetime import datetime, timedelta

    client = get_supabase_client()
    if not client:
        logger.warning("No Supabase client available for interaction check")
        return {
            'email_last_5_days': False,
            'call_last_10_days': False,
            'new_policy_last_30_days': False,
            'open_complaint': False,
            'claim_last_60_days': False
        }

    # Convert codice_cliente to integer if it's in format "CLI_XXXX"
    cliente_id = codice_cliente
    if isinstance(codice_cliente, str) and codice_cliente.startswith("CLI_"):
        try:
            cliente_id = int(codice_cliente.replace("CLI_", ""))
        except ValueError:
            logger.warning(f"Could not parse codice_cliente: {codice_cliente}")
            return {
                'email_last_5_days': False,
                'call_last_10_days': False,
                'new_policy_last_30_days': False,
                'open_complaint': False,
                'claim_last_60_days': False
            }

    now = datetime.now()

    # Calculate business days (approximation: 5/7 of calendar days)
    five_business_days = now - timedelta(days=7)  # ~5 business days
    ten_days = now - timedelta(days=10)
    thirty_days = now - timedelta(days=30)
    sixty_days = now - timedelta(days=60)

    indicators = {
        'email_last_5_days': False,
        'call_last_10_days': False,
        'new_policy_last_30_days': False,
        'open_complaint': False,
        'claim_last_60_days': False
    }

    try:
        # Check emails in last 5 business days
        try:
            email_response = _retry_query(
                lambda: client.table("interactions")
                .select("id")
                .eq("codice_cliente", cliente_id)
                .eq("tipo_interazione", "email")
                .gte("data_interazione", five_business_days.isoformat())
                .limit(1)
                .execute()
            )
            indicators['email_last_5_days'] = len(email_response.data) > 0
        except Exception as e:
            logger.debug(f"Could not check emails for {codice_cliente}: {e}")

        # Check phone calls in last 10 days
        try:
            call_response = _retry_query(
                lambda: client.table("interactions")
                .select("id")
                .eq("codice_cliente", cliente_id)
                .eq("tipo_interazione", "telefonata")
                .gte("data_interazione", ten_days.isoformat())
                .limit(1)
                .execute()
            )
            indicators['call_last_10_days'] = len(call_response.data) > 0
        except Exception as e:
            logger.debug(f"Could not check calls for {codice_cliente}: {e}")

        # Check new policies in last 30 days
        try:
            policy_response = _retry_query(
                lambda: client.table("polizze")
                .select("id")
                .eq("codice_cliente", cliente_id)
                .gte("data_emissione", thirty_days.isoformat())
                .limit(1)
                .execute()
            )
            indicators['new_policy_last_30_days'] = len(policy_response.data) > 0
        except Exception as e:
            logger.debug(f"Could not check policies for {codice_cliente}: {e}")

        # Check open complaints (reclamo with esito NULL or not 'risolto'/'chiuso')
        try:
            complaint_response = _retry_query(
                lambda: client.table("interactions")
                .select("id")
                .eq("codice_cliente", cliente_id)
                .eq("tipo_interazione", "reclamo")
                .is_("esito", "null")
                .limit(1)
                .execute()
            )
            # If no results with null esito, check for open statuses
            if len(complaint_response.data) == 0:
                complaint_response = _retry_query(
                    lambda: client.table("interactions")
                    .select("id")
                    .eq("codice_cliente", cliente_id)
                    .eq("tipo_interazione", "reclamo")
                    .not_.in_("esito", ["risolto", "chiuso"])
                    .limit(1)
                    .execute()
                )
            indicators['open_complaint'] = len(complaint_response.data) > 0
        except Exception as e:
            logger.debug(f"Could not check complaints for {codice_cliente}: {e}")

        # Check claims in last 60 days
        try:
            claim_response = _retry_query(
                lambda: client.table("sinistri")
                .select("data_sinistro")
                .eq("codice_cliente", cliente_id)
                .gte("data_sinistro", sixty_days.isoformat())
                .limit(1)
                .execute()
            )
            indicators['claim_last_60_days'] = len(claim_response.data) > 0
        except Exception as e:
            logger.debug(f"Could not check claims for {codice_cliente}: {e}")

        logger.debug(f"Interaction check for {codice_cliente}: {indicators}")
        return indicators

    except Exception as e:
        logger.error(f"Error checking interactions for {codice_cliente}: {e}")
        return indicators


def is_client_eligible_for_top20(codice_cliente: str) -> bool:
    """
    Check if a client is eligible for Top 20 list.

    A client is eligible ONLY if all interaction indicators are False.

    Args:
        codice_cliente: Client ID to check

    Returns:
        True if eligible (no recent interactions), False otherwise
    """
    indicators = check_client_interactions(codice_cliente)
    # Client is eligible only if NO indicator is True
    return not any(indicators.values())


def check_all_clients_interactions_batch(codici_clienti: list) -> Dict[str, Dict[str, bool]]:
    """
    Batch check interactions for multiple clients at once (much faster).

    Args:
        codici_clienti: List of client IDs to check

    Returns:
        Dictionary mapping codice_cliente -> indicators dict
    """
    from datetime import datetime, timedelta

    # Chunk size to avoid URL length issues (max ~100 IDs per query)
    BATCH_CHUNK_SIZE = 100

    client = get_supabase_client()
    if not client:
        logger.warning("No Supabase client available for batch interaction check")
        return {cc: {
            'email_last_5_days': False,
            'call_last_10_days': False,
            'new_policy_last_30_days': False,
            'open_complaint': False,
            'claim_last_60_days': False
        } for cc in codici_clienti}

    # Convert all client codes to integers
    cliente_ids = []
    cliente_map = {}  # Maps integer ID back to original string
    for cc in codici_clienti:
        if isinstance(cc, str) and cc.startswith("CLI_"):
            try:
                cid = int(cc.replace("CLI_", ""))
                cliente_ids.append(cid)
                cliente_map[cid] = cc
            except ValueError:
                logger.warning(f"Could not parse codice_cliente: {cc}")
        else:
            cliente_ids.append(cc)
            cliente_map[cc] = cc

    now = datetime.now()
    five_business_days = now - timedelta(days=7)
    ten_days = now - timedelta(days=10)
    thirty_days = now - timedelta(days=30)
    sixty_days = now - timedelta(days=60)

    # Initialize results
    results = {cc: {
        'email_last_5_days': False,
        'call_last_10_days': False,
        'new_policy_last_30_days': False,
        'open_complaint': False,
        'claim_last_60_days': False
    } for cc in codici_clienti}

    # Helper to chunk list
    def chunked(lst, size):
        for i in range(0, len(lst), size):
            yield lst[i:i + size]

    query_count = 0

    try:
        # Process in chunks to avoid URL length issues
        for chunk_ids in chunked(cliente_ids, BATCH_CHUNK_SIZE):
            # Batch query 1: All recent interactions (emails, calls, complaints)
            try:
                chunk_ids_copy = chunk_ids[:]  # Capture for lambda
                interactions_response = _retry_query(
                    lambda ids=chunk_ids_copy: client.table("interactions")
                    .select("codice_cliente, tipo_interazione, data_interazione, esito")
                    .in_("codice_cliente", ids)
                    .gte("data_interazione", five_business_days.isoformat())
                    .execute()
                )
                query_count += 1

                for row in interactions_response.data:
                    cc = cliente_map.get(row['codice_cliente'])
                    if not cc:
                        continue

                    tipo = row.get('tipo_interazione', '')
                    data = row.get('data_interazione', '')

                    # Check emails (last 5 business days)
                    if tipo == 'email' and data >= five_business_days.isoformat():
                        results[cc]['email_last_5_days'] = True

                    # Check calls (last 10 days)
                    if tipo == 'telefonata' and data >= ten_days.isoformat():
                        results[cc]['call_last_10_days'] = True

                    # Check open complaints
                    if tipo == 'reclamo':
                        esito = row.get('esito', '')
                        if not esito or esito not in ['risolto', 'chiuso']:
                            results[cc]['open_complaint'] = True
            except Exception as e:
                logger.debug(f"Error in batch interactions check for chunk: {e}")

            # Batch query 2: Recent policies
            try:
                chunk_ids_copy = chunk_ids[:]
                policies_response = _retry_query(
                    lambda ids=chunk_ids_copy: client.table("polizze")
                    .select("codice_cliente, data_emissione")
                    .in_("codice_cliente", ids)
                    .gte("data_emissione", thirty_days.isoformat())
                    .execute()
                )
                query_count += 1

                for row in policies_response.data:
                    cc = cliente_map.get(row['codice_cliente'])
                    if cc:
                        results[cc]['new_policy_last_30_days'] = True
            except Exception as e:
                logger.debug(f"Error in batch policies check for chunk: {e}")

            # Batch query 3: Recent claims
            try:
                chunk_ids_copy = chunk_ids[:]
                claims_response = _retry_query(
                    lambda ids=chunk_ids_copy: client.table("sinistri")
                    .select("codice_cliente, data_sinistro")
                    .in_("codice_cliente", ids)
                    .gte("data_sinistro", sixty_days.isoformat())
                    .execute()
                )
                query_count += 1

                for row in claims_response.data:
                    cc = cliente_map.get(row['codice_cliente'])
                    if cc:
                        results[cc]['claim_last_60_days'] = True
            except Exception as e:
                logger.debug(f"Error in batch claims check for chunk: {e}")

        logger.info(f"Batch checked interactions for {len(codici_clienti)} clients with {query_count} queries instead of {len(codici_clienti) * 5}")
        return results

    except Exception as e:
        logger.error(f"Error in batch interaction check: {e}")
        return results


def insert_phone_call_interaction(
    codice_cliente: str,
    polizza_proposta: str = None,
    esito: str = "neutro",
    note: str = "Chiamata effettuata da Top 5"
) -> bool:
    """
    Insert a new phone call interaction for a client.

    Args:
        codice_cliente: Client ID (can be string like "CLI_9500" or integer)
        polizza_proposta: The policy proposed during the call (optional)
        esito: Outcome of the call (positivo, neutro, negativo)
        note: Optional notes about the call

    Returns:
        True if successful, False otherwise
    """
    from datetime import datetime

    client = get_supabase_client()
    if not client:
        logger.error("No Supabase client available for inserting interaction")
        return False

    # Convert codice_cliente to integer
    cliente_id = codice_cliente
    if isinstance(codice_cliente, str) and codice_cliente.startswith("CLI_"):
        try:
            cliente_id = int(codice_cliente.replace("CLI_", ""))
        except ValueError:
            logger.error(f"Could not parse codice_cliente: {codice_cliente}")
            return False

    try:
        # Generate dedup key to avoid duplicates
        today = datetime.now().date().isoformat()
        dedup_key = f"{cliente_id}_telefonata_{today}"

        # Build motivo based on polizza_proposta
        motivo = "Contatto commerciale"
        if polizza_proposta:
            motivo = f"Proposta: {polizza_proposta}"

        interaction_data = {
            "codice_cliente": cliente_id,
            "data_interazione": today,
            "tipo_interazione": "telefonata",
            "motivo": motivo,
            "esito": esito,
            "note": note,
            "dedup_key": dedup_key
        }

        # Use upsert to update if exists, insert if not
        response = _retry_query(
            lambda: client.table("interactions").upsert(
                interaction_data,
                on_conflict="dedup_key"
            ).execute()
        )

        logger.info(f"Successfully upserted phone call interaction for client {codice_cliente}")
        return True

    except Exception as e:
        logger.error(f"Error upserting phone call interaction for {codice_cliente}: {e}")
        return False
