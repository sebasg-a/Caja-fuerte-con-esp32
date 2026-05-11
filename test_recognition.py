import cv2
import json
import os

MODEL_PATH = os.path.join("model", "lbph_model.yml")
LABELS_PATH = os.path.join("model", "labels.json")
TEST_IMAGE = "prueba.jpg"   # cambia esto por tu imagen de prueba

cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)

with open(LABELS_PATH, "r", encoding="utf-8") as f:
    LABEL_MAP = json.load(f)

img = cv2.imread(TEST_IMAGE)

if img is None:
    raise RuntimeError("No se pudo leer la imagen de prueba")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

print("Rostros detectados:", len(faces))

if len(faces) == 0:
    print("No se detecto ningun rostro")
else:
    x, y, w, h = faces[0]
    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (200, 200))

    label, confidence = recognizer.predict(face)

    print("Label:", label)
    print("Confidence:", confidence)

    if label == -1:
        print("Resultado: desconocido")
    else:
        persona = LABEL_MAP.get(str(label), "desconocido")
        print("Persona reconocida:", persona)