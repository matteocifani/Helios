#!/usr/bin/env python3
"""
Analisi avanzata dello screenshot centrale:
- ricava rilevamento pannelli solari (riusa lo script esistente)
- rileva piscine tramite soglia colore / contorni
- rileva aree verdi che sovrastano/toccano l'area centrale (possibile ombra/alberi)

Output:
- Python/yolo_results/advanced_analysis.json
- Python/yolo_results/advanced_annotated.png

Esegue lo script sulla `satellite_view.png` nella stessa cartella.
"""
import os
import sys
import json
import subprocess
import cv2
import numpy as np

ROOT = os.path.dirname(__file__)
IMG = os.path.join(ROOT, "satellite_view.png")
OUT_DIR = os.path.join(ROOT, "yolo_results")
os.makedirs(OUT_DIR, exist_ok=True)

def run_existing_solar_detector():
    # Chiama lo script esistente per ottenere le statistiche sui pannelli
    cmd = [sys.executable, os.path.join(ROOT, "solar_detector_yolov8.py"), "--source", IMG]
    try:
        subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("Attenzione: esecuzione detector pannelli ha fallito:", e)

    # Statistiche salvate da quello script
    stats_path = os.path.join(OUT_DIR, "satellite_view_solar_stats.json")
    if os.path.exists(stats_path):
        with open(stats_path, "r") as f:
            return json.load(f)
    return None

def detect_pools_and_trees(image_path):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # --- Pool detection (soglia blu/ciano) ---
    lower_blue = np.array([85, 50, 50])
    upper_blue = np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel, iterations=2)
    mask_blue = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pools = []
    for c in contours_blue:
        area = cv2.contourArea(c)
        if area < 800:  # filter small specks
            continue
        x,y,ww,hh = cv2.boundingRect(c)
        ar = ww/float(hh) if hh>0 else 0
        # le piscine possono essere rettangolari o ovali; accettiamo anche ar variabili
        pools.append({"area": int(area), "bbox": [int(x),int(y),int(ww),int(hh)], "aspect_ratio": float(ar)})

    # --- Tree detection (verde) ---
    lower_green = np.array([25, 40, 30])
    upper_green = np.array([95, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel2, iterations=1)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, kernel2, iterations=2)

    contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    greens = []
    for c in contours_green:
        area = cv2.contourArea(c)
        if area < 500: continue
        x,y,ww,hh = cv2.boundingRect(c)
        greens.append({"area": int(area), "bbox": [int(x),int(y),int(ww),int(hh)]})

    # Define central roof area as central box (50% width/height)
    cx, cy = w//2, h//2
    rw, rh = int(w*0.5), int(h*0.5)
    roof_box = (cx - rw//2, cy - rh//2, rw, rh)

    # Check overlap between green contours and roof_box -> possible overhanging trees
    def intersects(a, b):
        ax,ay,aw,ah = a
        bx,by,bw,bh = b
        return not (ax+aw < bx or bx+bw < ax or ay+ah < by or by+bh < ay)

    trees_overlapping = []
    for g in greens:
        if intersects(tuple(g["bbox"]), roof_box):
            trees_overlapping.append(g)

    # Annotate image
    anno = img.copy()
    # draw roof box
    rx,ry,rw_,rh_ = roof_box
    cv2.rectangle(anno, (rx,ry), (rx+rw_, ry+rh_), (200,200,0), 2)
    # draw pools in blue
    for p in pools:
        x,y,ww,hh = p["bbox"]
        cv2.rectangle(anno, (x,y), (x+ww,y+hh), (255,0,0), 2)
    # draw overlapping greens in red
    for t in trees_overlapping:
        x,y,ww,hh = t["bbox"]
        cv2.rectangle(anno, (x,y), (x+ww,y+hh), (0,0,255), 2)

    out_img = os.path.join(OUT_DIR, "advanced_annotated.png")
    cv2.imwrite(out_img, anno)

    return {
        "pools": pools,
        "greens": greens,
        "trees_overlapping": trees_overlapping,
        "roof_box": list(roof_box),
        "annotated_image": out_img
    }

def main():
    if not os.path.exists(IMG):
        print("Errore: immagine satellite_view.png non trovata nella cartella Python.")
        sys.exit(1)

    solar_stats = run_existing_solar_detector()
    other = detect_pools_and_trees(IMG)

    combined = {
        "solar_stats": solar_stats,
        "pools": other["pools"],
        "trees_overlapping": other["trees_overlapping"],
        "annotated_image": other["annotated_image"]
    }

    out_json = os.path.join(OUT_DIR, "advanced_analysis.json")
    with open(out_json, "w") as f:
        json.dump(combined, f, indent=2)

    print("Analisi completata.")
    print("Risultati JSON:", out_json)
    print("Immagine annotata:", other["annotated_image"])


if __name__ == '__main__':
    main()
