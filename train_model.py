import os
import json
import cv2
import numpy as np

DATASET_DIR = "dataset"
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "lbph_model.yml")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.json")

os.makedirs(MODEL_DIR, exist_ok=True)

cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

images = []
labels = []
label_map = {}
current_id = 0

for person_name in sorted(os.listdir(DATASET_DIR)):
    person_dir = os.path.join(DATASET_DIR, person_name)
    if not os.path.isdir(person_dir):
        continue

    label_map[current_id] = person_name

    for filename in os.listdir(person_dir):
        path = os.path.join(person_dir, filename)
        img = cv2.imread(path)

        if img is None:
            print("No se pudo leer:", path)
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            print("No se detecto rostro en:", path)
            continue

        x, y, w, h = faces[0]
        face = gray[y:y+h, x:x+w]
        face = cv2.resize(face, (200, 200))

        images.append(face)
        labels.append(current_id)
        print("Muestra agregada:", path)

    current_id += 1

if not images:
    raise RuntimeError("No se encontraron rostros validos en dataset/")

model = cv2.face.LBPHFaceRecognizer_create(
    radius=1,
    neighbors=8,
    grid_x=8,
    grid_y=8,
    threshold=70.0
)

model.train(images, np.array(labels))
model.save(MODEL_PATH)

with open(LABELS_PATH, "w", encoding="utf-8") as f:
    json.dump(label_map, f, ensure_ascii=False, indent=2)

print("Modelo entrenado correctamente")
print("Modelo guardado en:", MODEL_PATH)
print("Etiquetas guardadas en:", LABELS_PATH)
print("Total de muestras usadas:", len(images))