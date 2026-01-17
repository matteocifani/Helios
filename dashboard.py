import streamlit as st
import json
import pandas as pd
import folium
from streamlit_folium import folium_static

# Page configuration
st.set_page_config(page_title="NBO Dashboard", layout="wide", initial_sidebar_state="expanded")

# Load data
@st.cache_data
def load_data():
    with open('data/nbo_master.json', 'r') as f:
        data = json.load(f)
    return data

def calculate_recommendation_score(rec, weights):
    """Calculate weighted score for a recommendation"""
    components = rec['componenti']
    score = (
        components['retention_gain'] * weights['retention'] / 100 +
        components['redditivita'] * weights['redditivita'] / 100 +
        components['propensione'] * weights['propensione'] / 100
    )
    return score

def get_all_recommendations(data, weights):
    """Get all recommendations with scores across all clients"""
    all_recs = []
    for client in data:
        for rec in client['raccomandazioni']:
            score = calculate_recommendation_score(rec, weights)
            all_recs.append({
                'codice_cliente': client['codice_cliente'],
                'nome': client['anagrafica']['nome'],
                'cognome': client['anagrafica']['cognome'],
                'prodotto': rec['prodotto'],
                'area_bisogno': rec['area_bisogno'],
                'score': score,
                'client_data': client,
                'recommendation': rec
            })
    return sorted(all_recs, key=lambda x: x['score'], reverse=True)

def show_client_detail(client_data, recommendation):
    """Display detailed client information"""
    st.title(f"{client_data['anagrafica']['nome']} {client_data['anagrafica']['cognome']}")

    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

    # Client info
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Anagrafica")
        ana = client_data['anagrafica']
        st.write(f"**Età:** {ana['eta']} anni")
        st.write(f"**Indirizzo:** {ana['indirizzo']}")
        st.write(f"**Città:** {ana['citta']}")
        st.write(f"**Provincia:** {ana['provincia']}")
        st.write(f"**Regione:** {ana['regione']}")

        st.subheader("Metadata")
        meta = client_data['metadata']
        st.write(f"**Codice Cliente:** {client_data['codice_cliente']}")
        st.write(f"**Churn Attuale:** {meta['churn_attuale']:.4f}")
        st.write(f"**Numero Polizze Attuali:** {meta['num_polizze_attuali']}")
        st.write(f"**Cluster NBA:** {meta['cluster_nba']}")
        st.write(f"**Cluster Risposta:** {meta['cluster_risposta']}")
        st.write(f"**Satisfaction Score:** {meta['satisfaction_score']:.1f}")
        st.write(f"**Engagement Score:** {meta['engagement_score']:.1f}")
        st.write(f"**CLV Stimato:** €{meta['clv_stimato']:,}")

    with col2:
        st.subheader("Prodotti Posseduti")
        if meta['prodotti_posseduti']:
            for prod in meta['prodotti_posseduti']:
                st.write(f"- {prod}")
        else:
            st.write("Nessun prodotto posseduto")

        st.subheader("Raccomandazione Selezionata")
        st.write(f"**Prodotto:** {recommendation['prodotto']}")
        st.write(f"**Area Bisogno:** {recommendation['area_bisogno']}")

        st.subheader("Componenti Score")
        comp = recommendation['componenti']
        st.write(f"**Retention Gain:** {comp['retention_gain']:.1f}%")
        st.write(f"**Redditività:** {comp['redditivita']:.1f}%")
        st.write(f"**Propensione:** {comp['propensione']:.1f}%")
        st.write(f"**Affinità Cluster:** {comp['affinita_cluster']:.1f}%")

        st.subheader("Dettagli Churn")
        det = recommendation['dettagli']
        st.write(f"**Delta Churn:** {det['delta_churn']:.6f}")
        st.write(f"**Churn Prima:** {det['churn_prima']:.6f}")
        st.write(f"**Churn Dopo:** {det['churn_dopo']:.6f}")

    # Map
    st.subheader("Localizzazione")
    lat = client_data['anagrafica']['latitudine']
    lon = client_data['anagrafica']['longitudine']

    m = folium.Map(location=[lat, lon], zoom_start=13)
    folium.Marker(
        [lat, lon],
        popup=f"{ana['nome']} {ana['cognome']}<br>{ana['indirizzo']}<br>{ana['citta']}",
        tooltip=f"{ana['nome']} {ana['cognome']}",
        icon=folium.Icon(color='red', icon='home')
    ).add_to(m)

    folium_static(m, width=700, height=500)

    # All recommendations for this client
    st.subheader("Tutte le Raccomandazioni")
    recs_data = []
    for rec in client_data['raccomandazioni']:
        score = calculate_recommendation_score(rec, st.session_state.weights)
        recs_data.append({
            'Prodotto': rec['prodotto'],
            'Area Bisogno': rec['area_bisogno'],
            'Score': f"{score:.2f}",
            'Retention Gain': f"{rec['componenti']['retention_gain']:.1f}%",
            'Redditività': f"{rec['componenti']['redditivita']:.1f}%",
            'Propensione': f"{rec['componenti']['propensione']:.1f}%",
            'Affinità': f"{rec['componenti']['affinita_cluster']:.1f}%"
        })

    df_recs = pd.DataFrame(recs_data)
    st.dataframe(df_recs, use_container_width=True)

def show_dashboard(data):
    """Display main dashboard"""
    st.title("NBO Dashboard - Raccomandazioni Prodotti")

    # Sidebar for weight selection
    st.sidebar.header("Pesi delle Componenti")
    st.sidebar.write("Regola i pesi per calcolare lo score delle raccomandazioni")

    retention_weight = st.sidebar.slider(
        "Retention Gain",
        min_value=0.0,
        max_value=1.0,
        value=0.33,
        step=0.01,
        help="Peso per la componente Retention Gain"
    )

    redditivita_weight = st.sidebar.slider(
        "Redditività",
        min_value=0.0,
        max_value=1.0,
        value=0.33,
        step=0.01,
        help="Peso per la componente Redditività"
    )

    propensione_weight = st.sidebar.slider(
        "Propensione",
        min_value=0.0,
        max_value=1.0,
        value=0.34,
        step=0.01,
        help="Peso per la componente Propensione"
    )

    # Normalize weights to sum to 1
    total = retention_weight + redditivita_weight + propensione_weight
    if total > 0:
        retention_weight = retention_weight / total
        redditivita_weight = redditivita_weight / total
        propensione_weight = propensione_weight / total

    weights = {
        'retention': retention_weight,
        'redditivita': redditivita_weight,
        'propensione': propensione_weight
    }

    st.session_state.weights = weights

    # Display normalized weights
    st.sidebar.write("**Pesi Normalizzati:**")
    st.sidebar.write(f"Retention: {retention_weight:.2%}")
    st.sidebar.write(f"Redditività: {redditivita_weight:.2%}")
    st.sidebar.write(f"Propensione: {propensione_weight:.2%}")

    # Get all recommendations
    all_recommendations = get_all_recommendations(data, weights)

    # Top recommendations
    st.header("Top Raccomandazioni")

    # Number of recommendations to show
    top_n = st.number_input("Numero di raccomandazioni da visualizzare", min_value=5, max_value=100, value=20, step=5)

    # Create dataframe for display
    top_recs = all_recommendations[:top_n]

    # Display as clickable table
    for idx, rec in enumerate(top_recs):
        col1, col2, col3, col4 = st.columns([2, 2, 5, 1])

        with col1:
            st.write(f"**{rec['nome']} {rec['cognome']}**")

        with col2:
            st.write(f"*{rec['codice_cliente']}*")

        with col3:
            st.write(f"{rec['prodotto']}")

        with col4:
            st.write(f"**{rec['score']:.2f}**")
            if st.button("Dettagli", key=f"btn_{idx}"):
                st.session_state.page = 'detail'
                st.session_state.selected_client = rec['client_data']
                st.session_state.selected_recommendation = rec['recommendation']
                st.rerun()

        st.divider()

    # Summary statistics
    st.header("Statistiche")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Totale Clienti", len(data))

    with col2:
        st.metric("Totale Raccomandazioni", len(all_recommendations))

    with col3:
        avg_score = sum(r['score'] for r in all_recommendations) / len(all_recommendations)
        st.metric("Score Medio", f"{avg_score:.2f}")

    with col4:
        top_score = all_recommendations[0]['score'] if all_recommendations else 0
        st.metric("Score Massimo", f"{top_score:.2f}")

# Main application logic
def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'

    if 'weights' not in st.session_state:
        st.session_state.weights = {
            'retention': 0.33,
            'redditivita': 0.33,
            'propensione': 0.34
        }

    # Load data
    data = load_data()

    # Route to appropriate page
    if st.session_state.page == 'dashboard':
        show_dashboard(data)
    elif st.session_state.page == 'detail':
        show_client_detail(
            st.session_state.selected_client,
            st.session_state.selected_recommendation
        )

if __name__ == "__main__":
    main()
