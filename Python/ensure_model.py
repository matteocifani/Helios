from pathlib import Path

# Scarica/assicura il modello YOLOv8s-seg richiesto
MODEL_NAME = "yolov8s-seg.pt"
MODEL_PATH = Path(__file__).parent / "solar_panel_yolov8s.pt"

if MODEL_PATH.exists():
    print(f"Modello già presente: {MODEL_PATH}")
else:
    print("Modello non trovato localmente. Provo a scaricarlo usando ultralytics (yolov8s-seg)...")
    try:
        from ultralytics import YOLO
        # Caricamento del modello (se manca verrà scaricato)
        YOLO(MODEL_NAME)
        print("Download/modello disponibile: yolov8s-seg.pt (verifica che sia presente o rinomina se necessario)")
    except Exception as e:
        print("Impossibile scaricare il modello automaticamente:", e)
        print("Per favore posiziona manualmente il file 'solar_panel_yolov8s.pt' nella cartella Python/")
