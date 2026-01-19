**Formula modello stimato:**
```
logit(P(Sinistro)) = β0 + β1*Età + β2*Età² + β3*Metratura + 
                     β4*Sistema_Allarme + β5*Zona + β6*P_Furti + 
                     β7*log(Reddito) + ...

Frequenza_Predetta = 1 / (1 + exp(-logit))

Severità sinistri:

**Formula modello stimato:**
```
log(E[Costo | Sinistro]) = β0 + β1*log(Metratura) + β2*Sistema_Allarme + 
                           β3*Zona + β4*log(Patrimonio) + ...

Severità_Predetta = exp(log_severità)

Premio

# === CALCOLO PREMIO TECNICO ===
calcola_premio_tecnico <- function(frequenza, severita, 
                                   loading = 0.30, 
                                   loss_ratio_target = 0.70) {
  premio_puro <- frequenza * severita
  premio_tecnico <- premio_puro * (1 + loading) / (1 - loss_ratio_target)
  
  return(list(
    premio_puro = premio_puro,
    premio_tecnico = premio_tecnico,
    frequenza = frequenza,
    severita = severita
  ))
}

# Gap assoluto e relativo
      Gap_Assoluto = Premio_Totale_Annuo - Premio_Tecnico_Calc,
      Gap_Relativo_Perc = (Premio_Totale_Annuo - Premio_Tecnico_Calc) / Premio_Tecnico_Calc * 100,