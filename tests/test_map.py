"""
Test Minimal Map - Hardcoded data to isolate issue
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Minimal Map Test", layout="wide")
st.title("🗺️ Test Mappa Minimo")

# Hardcoded test data - Italian cities
data = {
    'city': ['Roma', 'Milano', 'Napoli', 'Torino', 'Palermo', 'Firenze', 'Bologna', 'Genova'],
    'lat': [41.9028, 45.4642, 40.8518, 45.0703, 38.1157, 43.7696, 44.4949, 44.4056],
    'lon': [12.4964, 9.1900, 14.2681, 7.6869, 13.3615, 11.2558, 11.3426, 8.9463]
}
df = pd.DataFrame(data)

st.write(f"**Test con {len(df)} città italiane hardcoded**")
st.dataframe(df)

st.subheader("🗺️ Mappa con st.map()")
st.map(df)

st.success("Se vedi 8 punti rossi sulle città italiane, st.map() funziona!")
