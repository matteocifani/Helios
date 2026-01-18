# Supabase Database Schema

Generated: 2026-01-18 18:01:39

## Tables Overview

| Table | Columns | Rows |
|-------|---------|------|
| [clienti](clienti.md) | 38 | 11200 |
| [polizze](polizze.md) | 22 | 18039 |
| [abitazioni](abitazioni.md) | 28 | 5190 |
| [sinistri](sinistri.md) | 9 | 1677 |
| [interactions](interactions.md) | 11 | 41182 |

## Table Details

### clienti

| Column | Type |
|--------|------|
| codice_cliente | integer |
| nome | text |
| cognome | text |
| eta | integer |
| luogo_nascita | text |
| luogo_residenza | text |
| professione | text |
| reddito | float |
| reddito_familiare | float |
| numero_figli | integer |
| anzianita_compagnia | integer |
| stato_civile | text |
| numero_familiari_carico | integer |
| reddito_stimato | float |
| patrimonio_finanziario_stimato | float |
| patrimonio_reale_stimato | float |
| consumi_stimati | float |
| propensione_vita | float |
| propensione_danni | float |
| valore_immobiliare_medio | float |
| probabilita_furti | float |
| probabilita_rapine | float |
| zona_residenza | text |
| agenzia | text |
| latitudine | float |
| longitudine | float |
| num_polizze | integer |
| engagement_score | float |
| churn_probability | float |
| clv_stimato | float |
| potenziale_crescita | float |
| reclami_totali | integer |
| satisfaction_score | float |
| data_ultima_visita | text |
| visite_ultimo_anno | integer |
| cluster_risposta | text |
| created_at | timestamp/date |
| updated_at | timestamp/date |

### polizze

| Column | Type |
|--------|------|
| id | integer |
| codice_cliente | integer |
| prodotto | text |
| area_bisogno | text |
| data_emissione | text |
| data_scadenza | text |
| premio_ricorrente | float |
| premio_unico | unknown (null) |
| capitale_rivalutato | float |
| massimale | unknown (null) |
| stato_polizza | text |
| canale_acquisizione | text |
| commissione_perc | float |
| premio_totale_annuo | float |
| commissione_euro | float |
| costi_operativi | float |
| margine_lordo | float |
| importo_liquidato | unknown (null) |
| sinistri_totali | integer |
| loss_ratio | integer |
| created_at | timestamp/date |
| updated_at | timestamp/date |

### abitazioni

| Column | Type |
|--------|------|
| id | integer |
| codice_cliente | integer |
| via | text |
| civico | text |
| citta | text |
| cap | unknown (null) |
| provincia | unknown (null) |
| paese | text |
| indirizzo_completo | text |
| latitudine | float |
| longitudine | float |
| fonte_dati | text |
| created_at | timestamp/date |
| updated_at | timestamp/date |
| metratura | float |
| sistema_allarme | boolean |
| zona_sismica | unknown (null) |
| hydro_risk_p3 | unknown (null) |
| hydro_risk_p2 | unknown (null) |
| flood_risk_p4 | unknown (null) |
| flood_risk_p3 | unknown (null) |
| solar_potential_kwh | unknown (null) |
| solar_coverage_percent | unknown (null) |
| solar_savings_euro | unknown (null) |
| high_solar_potential | boolean |
| risk_score | unknown (null) |
| high_risk_property | boolean |
| risk_category | unknown (null) |

### sinistri

| Column | Type |
|--------|------|
| codice_cliente | integer |
| data_sinistro | text |
| tipologia_sinistro | text |
| prodotto | text |
| area_bisogno | text |
| importo_liquidato | integer |
| stato_liquidazione | text |
| created_at | timestamp/date |
| updated_at | timestamp/date |

### interactions

| Column | Type |
|--------|------|
| id | integer |
| codice_cliente | integer |
| data_interazione | text |
| tipo_interazione | text |
| motivo | text |
| esito | text |
| note | text |
| text_embedded | text |
| embedding | text |
| dedup_key | text |
| created_at | timestamp/date |

