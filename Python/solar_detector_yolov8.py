"""
Solar Panel Detection usando YOLOv8s pre-addestrato (segmentazione).
Modello: finloop/yolov8s-seg-solar-panels (scaricato da HuggingFace)

Il modello è già addestrato su dataset Roboflow specifici per pannelli solari.
Questo è MOLTO più affidabile del modello COCO generico.

Uso:
python solar_detector_yolov8.py --source satellite_view.png

Output:
- Immagine annotata con mask dei pannelli solari
- JSON con statistiche (area pannelli, % copertura, numero istanze)
"""

import os
import json
import argparse
from ultralytics import YOLO
import cv2
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_inference_segmentation(source_path: str, model_path: str | None = None, conf=0.25, save_dir: str | None = None):
    if save_dir is None:
        save_dir = os.path.join(SCRIPT_DIR, "yolo_results")
    os.makedirs(save_dir, exist_ok=True)

    # Se model_path non è specificato, usa il modello pre-addestrato locale
    model_source = model_path if model_path is not None else os.path.join(SCRIPT_DIR, "solar_panel_yolov8s.pt")
    
    if not os.path.exists(model_source):
        print(f"Errore: modello non trovato in {model_source}")
        print(f"Scarica il modello: https://huggingface.co/finloop/yolov8s-seg-solar-panels/resolve/main/best.pt")
        return

    print(f"Loading model: {model_source}")
    model = YOLO(model_source)

    print(f"Running segmentation inference on: {source_path}")
    # task='segment' per instance segmentation
    results = model.predict(source=source_path, conf=conf, task='segment', verbose=False)
    
    res = results[0]
    img = cv2.imread(source_path)
    h, w = img.shape[:2]

    statistics = {
        'source': source_path,
        'total_area_pixels': h * w,
        'solar_panel_instances': 0,
        'solar_panel_area_pixels': 0,
        'coverage_percentage': 0.0,
        'masks': []
    }

    # Centro dell'immagine - le detection troppo lontane dal centro sono probabilmente etichette
    cx, cy = w // 2, h // 2
    max_distance_from_center = min(w, h) * 0.4  # 40% della dimensione minore

    # Estrai segmentazioni (mask)
    if hasattr(res, 'masks') and res.masks is not None:
        masks = res.masks.data
        confs = res.boxes.conf.cpu().numpy() if hasattr(res.boxes.conf, 'cpu') else res.boxes.conf.numpy()
        boxes = res.boxes.xyxy.cpu().numpy() if hasattr(res.boxes.xyxy, 'cpu') else res.boxes.xyxy.numpy()

        # Converti mask in numpy
        masks_np = masks.cpu().numpy() if hasattr(masks, 'cpu') else masks.numpy()
        
        total_solar_area = 0
        valid_count = 0
        
        for i, mask in enumerate(masks_np):
            # Ridimensiona mask alle dimensioni dell'immagine
            mask_resized = cv2.resize(mask.astype(np.float32), (w, h))
            mask_binary = (mask_resized > 0.5).astype(np.uint8)
            
            # Calcola il centro della detection usando il bounding box
            if i < len(boxes):
                x1, y1, x2, y2 = boxes[i]
                det_cx = (x1 + x2) / 2
                det_cy = (y1 + y2) / 2
                
                # Calcola distanza dal centro dell'immagine
                distance = ((det_cx - cx) ** 2 + (det_cy - cy) ** 2) ** 0.5
                
                # FILTRO: Ignora detection troppo lontane dal centro (probabilmente etichette)
                if distance > max_distance_from_center:
                    print(f"   Ignorata detection {i+1}: troppo lontana dal centro (dist={distance:.0f}px)")
                    continue
                
                # FILTRO: Ignora detection con aspect ratio molto anomalo (etichette tendono ad essere molto larghe)
                box_w = x2 - x1
                box_h = y2 - y1
                aspect_ratio = max(box_w, box_h) / (min(box_w, box_h) + 1)
                if aspect_ratio > 5:  # Troppo allungato, probabilmente testo
                    print(f"   Ignorata detection {i+1}: aspect ratio anomalo ({aspect_ratio:.1f})")
                    continue
            
            area = np.sum(mask_binary)
            confidence = float(confs[i]) if i < len(confs) else 0.0
            
            total_solar_area += area
            valid_count += 1
            
            # Colora la mask in blu/cyan (colore tipico pannelli)
            img[mask_binary == 1] = [255, 165, 0]  # Blu in BGR
            
            statistics['masks'].append({
                'instance': valid_count,
                'area_pixels': int(area),
                'confidence': confidence
            })

        statistics['solar_panel_instances'] = valid_count
        statistics['solar_panel_area_pixels'] = int(total_solar_area)
        statistics['coverage_percentage'] = round((total_solar_area / (h * w)) * 100, 2)

        # Scrivi statistiche sull'immagine
        text = f"Solar Panels: {statistics['solar_panel_instances']} | Coverage: {statistics['coverage_percentage']}%"
        cv2.putText(img, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    else:
        print("Nessun pannello solare rilevato nell'immagine.")

    # Salva risultati
    base = os.path.splitext(os.path.basename(source_path))[0]
    out_img = os.path.join(save_dir, f"{base}_solar_annotated.png")
    out_json = os.path.join(save_dir, f"{base}_solar_stats.json")

    cv2.imwrite(out_img, img)
    with open(out_json, 'w') as f:
        json.dump(statistics, f, indent=2)

    print(f"\n=== RISULTATI ===")
    print(f"Pannelli solari rilevati: {statistics['solar_panel_instances']}")
    print(f"Area pannelli: {statistics['solar_panel_area_pixels']} pixels")
    print(f"Copertura tetto: {statistics['coverage_percentage']}%")
    print(f"\nImmagine annotata: {out_img}")
    print(f"Statistiche JSON: {out_json}")


def train_yolo(data_yaml: str, model='yolov8n.pt', epochs=50, imgsz=640, batch=16):
    """Helper che avvia il training/fine-tuning con Ultralytics YOLOv8.
    `data_yaml` deve essere il file di configurazione dataset (stile YOLO/Ultralytics).
    Esempio semplice di chiamata:
        train_yolo('dataset/data.yaml', model='yolov8n.pt', epochs=50)
    """
    print(f"Starting training: model={model}, data={data_yaml}, epochs={epochs}")
    ymodel = YOLO(model)
    ymodel.train(data=data_yaml, epochs=epochs, imgsz=imgsz, batch=batch)
    print("Training finished")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default=os.path.join(SCRIPT_DIR, 'satellite_view.png'), help='Image path')
    parser.add_argument('--model', type=str, default=None, help='Path to YOLO model weights (.pt)')
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--iou', type=float, default=0.45)
    parser.add_argument('--train', action='store_true', help='Run training helper (requires --data)')
    parser.add_argument('--data', type=str, help='Dataset YAML for training')
    parser.add_argument('--epochs', type=int, default=50)
    args = parser.parse_args()

    if args.train:
        if not args.data:
            print('Per training serve --data dataset/data.yaml')
            return
        train_yolo(data_yaml=args.data, model=args.model if args.model else 'yolov8n.pt', epochs=args.epochs)
        return

    if not os.path.exists(args.source):
        print(f"Fonte non trovata: {args.source}")
        return

    run_inference_segmentation(args.source, model_path=args.model, conf=args.conf)


if __name__ == '__main__':
    main()
