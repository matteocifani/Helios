library(tidyverse)
library(jsonlite)

# ============================================
# 0. LOAD REAL DATA
# ============================================

source("load_data.r")

set.seed(42)

# ============================================
# 1. ITALIAN REGIONS & CITIES DATA
# ============================================

# Realistic Italian cities with regions, provinces, and coordinates
ITALIAN_CITIES <- tribble(
  ~city, ~province, ~region, ~lat, ~lon,
  "Roma", "Roma", "Lazio", 41.9028, 12.4964,
  "Milano", "Milano", "Lombardia", 45.4642, 9.1900,
  "Napoli", "Napoli", "Campania", 40.8518, 14.2681,
  "Torino", "Torino", "Piemonte", 45.0703, 7.6869,
  "Palermo", "Palermo", "Sicilia", 38.1157, 13.3615,
  "Genova", "Genova", "Liguria", 44.4056, 8.9463,
  "Bologna", "Bologna", "Emilia-Romagna", 44.4949, 11.3426,
  "Firenze", "Firenze", "Toscana", 43.7696, 11.2558,
  "Bari", "Bari", "Puglia", 41.1171, 16.8719,
  "Catania", "Catania", "Sicilia", 37.5079, 15.0830,
  "Venezia", "Venezia", "Veneto", 45.4408, 12.3155,
  "Verona", "Verona", "Veneto", 45.4384, 10.9916,
  "Messina", "Messina", "Sicilia", 38.1938, 15.5540,
  "Padova", "Padova", "Veneto", 45.4064, 11.8768,
  "Trieste", "Trieste", "Friuli-Venezia Giulia", 45.6495, 13.7768,
  "Brescia", "Brescia", "Lombardia", 45.5416, 10.2118,
  "Taranto", "Taranto", "Puglia", 40.4668, 17.2472,
  "Prato", "Prato", "Toscana", 43.8777, 11.1021,
  "Parma", "Parma", "Emilia-Romagna", 44.8015, 10.3279,
  "Modena", "Modena", "Emilia-Romagna", 44.6471, 10.9252,
  "Reggio Calabria", "Reggio Calabria", "Calabria", 38.1113, 15.6476,
  "Reggio Emilia", "Reggio Emilia", "Emilia-Romagna", 44.6989, 10.6297,
  "Perugia", "Perugia", "Umbria", 43.1107, 12.3908,
  "Livorno", "Livorno", "Toscana", 43.5485, 10.3106,
  "Ravenna", "Ravenna", "Emilia-Romagna", 44.4184, 12.2035,
  "Cagliari", "Cagliari", "Sardegna", 39.2238, 9.1217,
  "Foggia", "Foggia", "Puglia", 41.4621, 15.5444,
  "Rimini", "Rimini", "Emilia-Romagna", 44.0678, 12.5695,
  "Salerno", "Salerno", "Campania", 40.6824, 14.7681,
  "Ferrara", "Ferrara", "Emilia-Romagna", 44.8381, 11.6198,
  "Sassari", "Sassari", "Sardegna", 40.7259, 8.5594,
  "Latina", "Latina", "Lazio", 41.4677, 12.9037,
  "Giugliano in Campania", "Napoli", "Campania", 40.9286, 14.1936,
  "Monza", "Monza e Brianza", "Lombardia", 45.5845, 9.2744,
  "Siracusa", "Siracusa", "Sicilia", 37.0755, 15.2866,
  "Pescara", "Pescara", "Abruzzo", 42.4584, 14.2139,
  "Bergamo", "Bergamo", "Lombardia", 45.6983, 9.6773,
  "Forlì", "Forlì-Cesena", "Emilia-Romagna", 44.2226, 12.0408,
  "Trento", "Trento", "Trentino-Alto Adige", 46.0664, 11.1257,
  "Vicenza", "Vicenza", "Veneto", 45.5455, 11.5354,
  "Terni", "Terni", "Umbria", 42.5635, 12.5154,
  "Bolzano", "Bolzano", "Trentino-Alto Adige", 46.4983, 11.3548,
  "Novara", "Novara", "Piemonte", 45.4469, 8.6220,
  "Piacenza", "Piacenza", "Emilia-Romagna", 45.0526, 9.6926,
  "Ancona", "Ancona", "Marche", 43.6158, 13.5189,
  "Andria", "Barletta-Andria-Trani", "Puglia", 41.2266, 16.2955,
  "Arezzo", "Arezzo", "Toscana", 43.4632, 11.8796,
  "Udine", "Udine", "Friuli-Venezia Giulia", 46.0710, 13.2345,
  "Cesena", "Forlì-Cesena", "Emilia-Romagna", 44.1396, 12.2431,
  "Lecce", "Lecce", "Puglia", 40.3515, 18.1750
)

# Function to assign random city with address details
genera_indirizzo <- function(n) {
  cities_sample <- ITALIAN_CITIES[sample(nrow(ITALIAN_CITIES), n, replace = TRUE), ]

  # Generate street addresses
  street_names <- c("Via Roma", "Via Garibaldi", "Via Mazzini", "Corso Italia", "Via Dante",
                    "Via Cavour", "Piazza Municipio", "Via Nazionale", "Via Verdi", "Corso Vittorio Emanuele",
                    "Via XX Settembre", "Via Milano", "Via Torino", "Via Venezia", "Viale della Repubblica")

  tibble(
    indirizzo = paste0(sample(street_names, n, replace = TRUE), ", ", sample(1:200, n, replace = TRUE)),
    citta = cities_sample$city,
    provincia = cities_sample$province,
    regione = cities_sample$region,
    latitudine = cities_sample$lat + rnorm(n, 0, 0.05),  # Add small random offset
    longitudine = cities_sample$lon + rnorm(n, 0, 0.05)
  )
}

# ============================================
# 2. PROFITABILITY TABLE (Simulated)
# ============================================

# Realistic profitability by product based on typical insurance margins
PROFITABILITY_TABLE <- tribble(
  ~prodotto, ~area_bisogno, ~margine_medio_annuo, ~redditivita_norm,
  "Assicurazione Casa e Famiglia: Casa Serena", "Protezione", 450, 0.75,
  "Assicurazione Salute e Benessere: Salute Protetta", "Protezione", 520, 0.87,
  "Polizza Vita a Premio Unico: Futuro Sicuro", "Risparmio e Investimento", 600, 1.00,
  "Polizza Vita a Premi Ricorrenti: Risparmio Costante", "Risparmio e Investimento", 380, 0.63,
  "Polizza Previdenziale: Pensione Serenità", "Previdenza", 540, 0.90
)

# ============================================
# 3. CHURN MODEL PARAMETERS (Simulated Logit)
# ============================================

# Simulated logistic regression coefficients
CHURN_MODEL_PARAMS <- list(
  intercept = -0.5,
  coef_num_polizze = -0.42,      # More policies = less churn
  coef_anzianita = -0.08,        # More years = less churn
  coef_visite = -0.15,           # More visits = less churn
  coef_satisfaction = -0.025,    # Higher satisfaction = less churn
  coef_reclami = 0.35,           # More complaints = more churn
  coef_eta = 0.015,              # Older = slightly more churn
  coef_reddito = -0.00001,       # Higher income = less churn (scaled)
  coef_engagement = -0.018,      # Higher engagement = less churn
  coef_num_figli = -0.05,        # More children = less churn (family ties)
  coef_protezione = -0.25,       # Has protection products = less churn
  coef_risparmio = -0.30,        # Has investment products = less churn
  coef_previdenza = -0.35        # Has pension products = less churn (strongest)
)

# Function to calculate churn probability using logit
calcola_churn_logit <- function(num_polizze, anzianita, visite, satisfaction, reclami,
                                eta, reddito, engagement, num_figli,
                                has_protezione, has_risparmio, has_previdenza) {
  logit <- CHURN_MODEL_PARAMS$intercept +
    CHURN_MODEL_PARAMS$coef_num_polizze * num_polizze +
    CHURN_MODEL_PARAMS$coef_anzianita * anzianita +
    CHURN_MODEL_PARAMS$coef_visite * visite +
    CHURN_MODEL_PARAMS$coef_satisfaction * satisfaction +
    CHURN_MODEL_PARAMS$coef_reclami * reclami +
    CHURN_MODEL_PARAMS$coef_eta * eta +
    CHURN_MODEL_PARAMS$coef_reddito * reddito +
    CHURN_MODEL_PARAMS$coef_engagement * engagement +
    CHURN_MODEL_PARAMS$coef_num_figli * num_figli +
    CHURN_MODEL_PARAMS$coef_protezione * has_protezione +
    CHURN_MODEL_PARAMS$coef_risparmio * has_risparmio +
    CHURN_MODEL_PARAMS$coef_previdenza * has_previdenza

  # Convert logit to probability
  prob <- 1 / (1 + exp(-logit))
  return(prob)
}

# Function to calculate delta churn with new product
# This recalculates churn using the logit model with +1 product in the relevant area
calcola_delta_churn <- function(cliente_data, area_bisogno) {

  # Current churn (already calculated)
  churn_prima <- cliente_data$churn_probability_new

  # Simulate adding one product in the specified area
  num_polizze_dopo = cliente_data$num_polizze_attive + 1

  has_protezione_dopo = cliente_data$has_protezione
  has_risparmio_dopo = cliente_data$has_risparmio
  has_previdenza_dopo = cliente_data$has_previdenza

  # Update the relevant flag based on product area
  if (area_bisogno == "Protezione") {
    has_protezione_dopo = 1
  } else if (area_bisogno == "Risparmio e Investimento") {
    has_risparmio_dopo = 1
  } else if (area_bisogno == "Previdenza") {
    has_previdenza_dopo = 1
  }

  # Recalculate churn with new product
  churn_dopo <- calcola_churn_logit(
    num_polizze = num_polizze_dopo,
    anzianita = cliente_data$Anzianità.con.la.Compagnia,
    visite = cliente_data$Visite_Ultimo_Anno,
    satisfaction = cliente_data$Satisfaction_Score,
    reclami = cliente_data$Reclami_Totali,
    eta = cliente_data$Età,
    reddito = cliente_data$Reddito.Stimato,
    engagement = cliente_data$Engagement_Score,
    num_figli = cliente_data$Numero.Figli,
    has_protezione = has_protezione_dopo,
    has_risparmio = has_risparmio_dopo,
    has_previdenza = has_previdenza_dopo
  )

  delta <- churn_prima - churn_dopo

  return(list(
    delta_churn = delta,
    churn_prima = churn_prima,
    churn_dopo = churn_dopo
  ))
}

# ============================================
# 4. CLUSTER AFFINITY (NBA Segmentation)
# ============================================

# Define NBA cluster (different from Cluster_Risposta)
# Based on demographic + behavioral patterns
genera_cluster_nba <- function(eta, num_polizze, reddito_stimato, propensione_vita, propensione_danni) {
  # Simple clustering logic (in reality you'd use k-means or similar)
  cluster <- case_when(
    eta < 35 & reddito_stimato < 40000 ~ 1,  # Young, low income
    eta < 35 & reddito_stimato >= 40000 ~ 2, # Young, high income
    eta >= 35 & eta < 55 & num_polizze <= 2 ~ 3, # Middle age, low engagement
    eta >= 35 & eta < 55 & num_polizze > 2 ~ 4,  # Middle age, high engagement
    eta >= 55 & propensione_vita > 0.6 ~ 5,  # Senior, investment-focused
    eta >= 55 & propensione_danni > 0.6 ~ 6, # Senior, protection-focused
    TRUE ~ 7  # Other
  )
  return(cluster)
}

# Penetration/affinity by cluster and product area
CLUSTER_AFFINITY <- tribble(
  ~cluster_nba, ~area_bisogno, ~penetrazione, ~affinita_norm,
  1, "Protezione", 0.45, 0.75,
  1, "Risparmio e Investimento", 0.25, 0.42,
  1, "Previdenza", 0.15, 0.25,
  2, "Protezione", 0.30, 0.50,
  2, "Risparmio e Investimento", 0.50, 0.83,
  2, "Previdenza", 0.35, 0.58,
  3, "Protezione", 0.55, 0.92,
  3, "Risparmio e Investimento", 0.20, 0.33,
  3, "Previdenza", 0.18, 0.30,
  4, "Protezione", 0.40, 0.67,
  4, "Risparmio e Investimento", 0.45, 0.75,
  4, "Previdenza", 0.40, 0.67,
  5, "Protezione", 0.25, 0.42,
  5, "Risparmio e Investimento", 0.60, 1.00,
  5, "Previdenza", 0.55, 0.92,
  6, "Protezione", 0.65, 1.00,
  6, "Risparmio e Investimento", 0.30, 0.50,
  6, "Previdenza", 0.45, 0.75,
  7, "Protezione", 0.40, 0.67,
  7, "Risparmio e Investimento", 0.35, 0.58,
  7, "Previdenza", 0.30, 0.50
)

# ============================================
# 5. PREPARE CLIENT DATA
# ============================================

# Add addresses to clients
indirizzi <- genera_indirizzo(nrow(clienti))
clienti <- bind_cols(clienti, indirizzi)

# Extract product ownership from polizze
prodotti_per_cliente <- polizze %>%
  filter(Stato_Polizza == "Attiva") %>%
  group_by(codice_cliente) %>%
  summarise(
    prodotti_posseduti = list(unique(Prodotto)),
    num_polizze_attive = n(),
    .groups = "drop"
  )

# Join with clients
clienti_enriched <- clienti %>%
  left_join(prodotti_per_cliente, by = "codice_cliente") %>%
  mutate(
    prodotti_posseduti = map(prodotti_posseduti, ~if(is.null(.x)) character(0) else .x),
    num_polizze_attive = replace_na(num_polizze_attive, 0)
  )

# Calculate product area flags for churn model
clienti_enriched <- clienti_enriched %>%
  mutate(
    has_protezione = map_lgl(prodotti_posseduti, ~{
      any(str_detect(.x, "Casa Serena|Salute Protetta|Protezione Stradale|Sicurezza Personale"))
    }),
    has_risparmio = map_lgl(prodotti_posseduti, ~{
      any(str_detect(.x, "Futuro Sicuro|Risparmio Costante"))
    }),
    has_previdenza = map_lgl(prodotti_posseduti, ~{
      any(str_detect(.x, "Pensione Serenità"))
    })
  )

# Generate NBA cluster
clienti_enriched <- clienti_enriched %>%
  mutate(
    cluster_nba = genera_cluster_nba(
      Età,
      num_polizze_attive,
      Reddito.Stimato,
      Propensione.Acquisto.Prodotti.Vita,
      Propensione.Acquisto.Prodotti.Danni
    )
  )

# Recalculate churn with logit model
clienti_enriched <- clienti_enriched %>%
  mutate(
    churn_probability_new = calcola_churn_logit(
      num_polizze = num_polizze_attive,
      anzianita = Anzianità.con.la.Compagnia,
      visite = Visite_Ultimo_Anno,
      satisfaction = Satisfaction_Score,
      reclami = Reclami_Totali,
      eta = Età,
      reddito = Reddito.Stimato,
      engagement = Engagement_Score,
      num_figli = Numero.Figli,
      has_protezione = as.numeric(has_protezione),
      has_risparmio = as.numeric(has_risparmio),
      has_previdenza = as.numeric(has_previdenza)
    )
  )

# ============================================
# 6. GENERATE NBO RECOMMENDATIONS
# ============================================

genera_raccomandazioni_nbo <- function(cliente_row) {

  codice <- cliente_row$codice_cliente
  cluster_nba <- cliente_row$cluster_nba
  cluster_risposta <- cliente_row$Cluster_Risposta
  churn_attuale <- cliente_row$churn_probability_new
  num_polizze <- cliente_row$num_polizze_attive
  propensione_vita <- cliente_row$Propensione.Acquisto.Prodotti.Vita
  propensione_danni <- cliente_row$Propensione.Acquisto.Prodotti.Danni
  prodotti_poss <- cliente_row$prodotti_posseduti[[1]]

  # Get all products from profitability table
  raccomandazioni <- PROFITABILITY_TABLE %>%
    left_join(
      CLUSTER_AFFINITY %>% filter(cluster_nba == !!cluster_nba),
      by = "area_bisogno"
    ) %>%
    mutate(
      # Calculate propensity score based on area (0-100)
      propensione_score = case_when(
        str_detect(area_bisogno, "Risparmio|Investimento") ~ propensione_vita * 100,
        str_detect(area_bisogno, "Protezione") ~ propensione_danni * 100,
        str_detect(area_bisogno, "Previdenza") ~ (propensione_vita * 0.7 + propensione_danni * 0.3) * 100,
        TRUE ~ 50
      ),

      # Calculate retention gain using logit model
      delta_churn_calc = map(area_bisogno, ~calcola_delta_churn(cliente_row, .x)),
      delta_churn_value = map_dbl(delta_churn_calc, ~.x$delta_churn),
      churn_prima = map_dbl(delta_churn_calc, ~.x$churn_prima),
      churn_dopo = map_dbl(delta_churn_calc, ~.x$churn_dopo),

      # Normalize retention gain to 0-100 scale
      retention_gain_score = (delta_churn_value / max(delta_churn_value, 0.001)) * 100,

      # Profitability score (already 0-1, scale to 0-100)
      redditivita_score = redditivita_norm * 100,

      # Affinity/cluster score (0-100)
      affinita_cluster_score = replace_na(affinita_norm * 100, 50)
    ) %>%
    # Don't calculate weighted score here - dashboard will do it
    # Just sort by a reasonable default for display
    arrange(desc(retention_gain_score + redditivita_score + propensione_score + affinita_cluster_score)) %>%
    select(
      area_bisogno,
      prodotto,
      retention_gain_score,
      redditivita_score,
      propensione_score,
      affinita_cluster_score,
      delta_churn = delta_churn_value,
      churn_prima,
      churn_dopo
    )

  # Filter out owned products
  raccomandazioni_filtrate <- raccomandazioni %>%
    filter(!prodotto %in% prodotti_poss)

  # Convert to list format for JSON
  racc_list <- raccomandazioni_filtrate %>%
    rowwise() %>%
    mutate(
      racc_obj = list(list(
        area_bisogno = area_bisogno,
        prodotto = prodotto,
        componenti = list(
          retention_gain = round(retention_gain_score, 1),
          redditivita = round(redditivita_score, 1),
          propensione = round(propensione_score, 1),
          affinita_cluster = round(affinita_cluster_score, 1)
        ),
        dettagli = list(
          delta_churn = round(delta_churn, 4),
          churn_prima = round(churn_prima, 4),
          churn_dopo = round(churn_dopo, 4)
        )
      ))
    ) %>%
    pull(racc_obj)

  return(racc_list)
}

# ============================================
# 7. BUILD MASTER JSON
# ============================================

cat("Generating NBO recommendations for all clients...\n")

# Generate for all clients (or subset for testing)
clienti_sample <- clienti_enriched %>% head(100)  # Change to nrow(clienti_enriched) for all

nbo_master_list <- list()


for (i in 1:nrow(clienti_sample)) {
  if (i %% 10 == 0) cat(sprintf("Processing client %d/%d\n", i, nrow(clienti_sample)))

  cliente <- clienti_sample[i, ]
  raccomandazioni <- genera_raccomandazioni_nbo(cliente)

  # Build JSON object for this client
  cliente_json <- list(
    codice_cliente = paste0("CLI_", cliente$codice_cliente),
    timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ"),

    # Client metadata
    anagrafica = list(
      nome = cliente$Nome,
      cognome = cliente$Cognome,
      eta = cliente$Età,
      indirizzo = cliente$indirizzo,
      citta = cliente$citta,
      provincia = cliente$provincia,
      regione = cliente$regione,
      latitudine = round(cliente$latitudine, 6),
      longitudine = round(cliente$longitudine, 6)
    ),

    # Recommendations
    raccomandazioni = raccomandazioni,

    # Metadata
    metadata = list(
      churn_attuale = round(cliente$churn_probability_new, 4),
      num_polizze_attuali = cliente$num_polizze_attive,
      cluster_nba = cliente$cluster_nba,
      cluster_risposta = as.character(cliente$Cluster_Risposta),
      prodotti_posseduti = cliente$prodotti_posseduti[[1]],
      satisfaction_score = cliente$Satisfaction_Score,
      engagement_score = cliente$Engagement_Score,
      clv_stimato = cliente$CLV_Stimato
    )
  )

  nbo_master_list[[i]] <- cliente_json
}

# ============================================
# 8. EXTRACT DISTRIBUTION DATA FOR ANALYSIS
# ============================================

cat("\nExtracting distribution data...\n")

# Extract all component scores from recommendations
all_scores <- map_dfr(nbo_master_list, function(cliente) {
  cliente_code <- cliente$codice_cliente
  churn <- cliente$metadata$churn_attuale
  cluster_nba <- cliente$metadata$cluster_nba
  cluster_risposta <- cliente$metadata$cluster_risposta
  num_polizze <- cliente$metadata$num_polizze_attuali

  if (length(cliente$raccomandazioni) == 0) return(tibble())

  map_dfr(cliente$raccomandazioni, function(racc) {
    tibble(
      codice_cliente = cliente_code,
      churn_attuale = churn,
      cluster_nba = cluster_nba,
      cluster_risposta = cluster_risposta,
      num_polizze_attuali = num_polizze,
      area_bisogno = racc$area_bisogno,
      prodotto = racc$prodotto,
      retention_gain = racc$componenti$retention_gain,
      redditivita = racc$componenti$redditivita,
      propensione = racc$componenti$propensione,
      affinita_cluster = racc$componenti$affinita_cluster,
      delta_churn = racc$dettagli$delta_churn,
      churn_prima = racc$dettagli$churn_prima,
      churn_dopo = racc$dettagli$churn_dopo
    )
  })
})

# ============================================
# 9. SAVE OUTPUT
# ============================================

# Save as JSON
output_json <- toJSON(nbo_master_list, pretty = TRUE, auto_unbox = TRUE)
write(output_json, "../../data/nbo_master.json")

# Save distribution data as CSV for analysis
write_csv(all_scores, "../../data/nbo_scores_distribution.csv")

cat("\n✓ Master JSON saved to: data/nbo_master.json\n")
cat("✓ Distribution data saved to: data/nbo_scores_distribution.csv\n")
cat(sprintf("✓ Total clients processed: %d\n", length(nbo_master_list)))

# ============================================
# 10. DISTRIBUTION ANALYSIS & SUMMARY
# ============================================

cat("\n" , rep("=", 70), "\n", sep = "")
cat("                    DISTRIBUTION ANALYSIS\n")
cat(rep("=", 70), "\n\n", sep = "")

# Churn Distribution
cat("━━━ CHURN PROBABILITY DISTRIBUTION ━━━\n")
churn_stats <- all_scores %>%
  distinct(codice_cliente, .keep_all = TRUE) %>%
  pull(churn_attuale)

cat(sprintf("  Mean:        %.4f\n", mean(churn_stats)))
cat(sprintf("  Median:      %.4f\n", median(churn_stats)))
cat(sprintf("  Std Dev:     %.4f\n", sd(churn_stats)))
cat(sprintf("  Min:         %.4f\n", min(churn_stats)))
cat(sprintf("  Max:         %.4f\n", max(churn_stats)))
cat("\n  Quantiles:\n")
quantiles <- quantile(churn_stats, probs = c(0.1, 0.25, 0.5, 0.75, 0.9))
for (i in seq_along(quantiles)) {
  cat(sprintf("    %s:  %.4f\n", names(quantiles)[i], quantiles[i]))
}

# Delta Churn Distribution
cat("\n━━━ DELTA CHURN (Retention Gain) DISTRIBUTION ━━━\n")
cat(sprintf("  Mean:        %.4f\n", mean(all_scores$delta_churn)))
cat(sprintf("  Median:      %.4f\n", median(all_scores$delta_churn)))
cat(sprintf("  Std Dev:     %.4f\n", sd(all_scores$delta_churn)))
cat(sprintf("  Min:         %.4f\n", min(all_scores$delta_churn)))
cat(sprintf("  Max:         %.4f\n", max(all_scores$delta_churn)))

delta_by_area <- all_scores %>%
  group_by(area_bisogno) %>%
  summarise(
    mean_delta = mean(delta_churn),
    median_delta = median(delta_churn),
    .groups = "drop"
  )
cat("\n  By Product Area:\n")
for (i in 1:nrow(delta_by_area)) {
  cat(sprintf("    %-30s  Mean: %.4f  Median: %.4f\n",
              delta_by_area$area_bisogno[i],
              delta_by_area$mean_delta[i],
              delta_by_area$median_delta[i]))
}

# Component Scores Distribution
cat("\n━━━ COMPONENT SCORES DISTRIBUTION (0-100 scale) ━━━\n")
cat("\n  Retention Gain:\n")
cat(sprintf("    Mean:   %.2f\n", mean(all_scores$retention_gain)))
cat(sprintf("    Median: %.2f\n", median(all_scores$retention_gain)))
cat(sprintf("    Std:    %.2f\n", sd(all_scores$retention_gain)))

cat("\n  Profitability:\n")
cat(sprintf("    Mean:   %.2f\n", mean(all_scores$redditivita)))
cat(sprintf("    Median: %.2f\n", median(all_scores$redditivita)))
cat(sprintf("    Std:    %.2f\n", sd(all_scores$redditivita)))

cat("\n  Propensity:\n")
cat(sprintf("    Mean:   %.2f\n", mean(all_scores$propensione)))
cat(sprintf("    Median: %.2f\n", median(all_scores$propensione)))
cat(sprintf("    Std:    %.2f\n", sd(all_scores$propensione)))

cat("\n  Cluster Affinity:\n")
cat(sprintf("    Mean:   %.2f\n", mean(all_scores$affinita_cluster)))
cat(sprintf("    Median: %.2f\n", median(all_scores$affinita_cluster)))
cat(sprintf("    Std:    %.2f\n", sd(all_scores$affinita_cluster)))

# Cluster Distribution
cat("\n━━━ CLUSTER DISTRIBUTION ━━━\n")
cluster_dist <- all_scores %>%
  distinct(codice_cliente, .keep_all = TRUE) %>%
  count(cluster_nba) %>%
  mutate(pct = n / sum(n) * 100)

cat("\n  NBA Clusters:\n")
for (i in 1:nrow(cluster_dist)) {
  cat(sprintf("    Cluster %d:  %4d clients  (%.1f%%)\n",
              cluster_dist$cluster_nba[i],
              cluster_dist$n[i],
              cluster_dist$pct[i]))
}

# Product recommendations distribution
cat("\n━━━ PRODUCT RECOMMENDATIONS DISTRIBUTION ━━━\n")
prod_dist <- all_scores %>%
  count(prodotto, area_bisogno) %>%
  arrange(desc(n))

cat("\n  Most Recommended Products:\n")
for (i in 1:min(nrow(prod_dist), 5)) {
  cat(sprintf("    %2d. %-50s  %4d times\n",
              i,
              prod_dist$prodotto[i],
              prod_dist$n[i]))
}

# Area distribution
cat("\n  By Product Area:\n")
area_dist <- all_scores %>%
  count(area_bisogno) %>%
  mutate(pct = n / sum(n) * 100) %>%
  arrange(desc(n))

for (i in 1:nrow(area_dist)) {
  cat(sprintf("    %-30s  %5d recommendations  (%.1f%%)\n",
              area_dist$area_bisogno[i],
              area_dist$n[i],
              area_dist$pct[i]))
}

# Correlation analysis
cat("\n━━━ COMPONENT CORRELATIONS ━━━\n")
cor_matrix <- cor(all_scores %>% select(retention_gain, redditivita, propensione, affinita_cluster))
cat("\n")
cat("                  Retention  Profit  Propensity  Affinity\n")
cat("  Retention Gain    1.000    ")
cat(sprintf("%.3f     %.3f      %.3f\n",
            cor_matrix[1,2], cor_matrix[1,3], cor_matrix[1,4]))
cat("  Profitability     ")
cat(sprintf("%.3f    1.000     %.3f      %.3f\n",
            cor_matrix[2,1], cor_matrix[2,3], cor_matrix[2,4]))
cat("  Propensity        ")
cat(sprintf("%.3f    %.3f     1.000      %.3f\n",
            cor_matrix[3,1], cor_matrix[3,2], cor_matrix[3,4]))
cat("  Cluster Affinity  ")
cat(sprintf("%.3f    %.3f     %.3f      1.000\n",
            cor_matrix[4,1], cor_matrix[4,2], cor_matrix[4,3]))

cat("\n" , rep("=", 70), "\n", sep = "")
cat("\n=== Sample output (first client) ===\n")
cat(toJSON(nbo_master_list[[1]], pretty = TRUE, auto_unbox = TRUE))
cat("\n")
