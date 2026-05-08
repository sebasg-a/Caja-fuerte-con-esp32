from flask import Flask, request, jsonify, send_from_directory
import os
import json
import cv2
from datetime import datetime

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5000))
SAVE_DIR = os.environ.get("UPLOAD_DIR", "recibidas")
EVENTS_FILE = os.path.join(SAVE_DIR, "eventos.json")

MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "lbph_model.yml")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.json")

os.makedirs(SAVE_DIR, exist_ok=True)

cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)

with open(LABELS_PATH, "r", encoding="utf-8") as f:
    LABEL_MAP = json.load(f)

def cargar_eventos():
    if not os.path.exists(EVENTS_FILE):
        return []
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_eventos(eventos):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)

def registrar_evento(filename, accion, ip_origen, resultado, persona, confianza):
    eventos = cargar_eventos()

    evento = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename,
        "accion": accion,
        "resultado": resultado,
        "persona": persona,
        "confianza": confianza,
        "ip_origen": ip_origen
    }

    eventos.insert(0, evento)
    guardar_eventos(eventos)

def reconocer_persona(filepath):
    img = cv2.imread(filepath)

    if img is None:
        return {
            "accion": "rechazar",
            "resultado": "error_imagen",
            "persona": "desconocido",
            "confianza": None
        }

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        return {
            "accion": "rechazar",
            "resultado": "sin_rostro",
            "persona": "desconocido",
            "confianza": None
        }

    x, y, w, h = faces[0]
    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (200, 200))

    label, confidence = recognizer.predict(face)

    if label == -1:
        return {
            "accion": "rechazar",
            "resultado": "intento_fallido",
            "persona": "desconocido",
            "confianza": float(confidence)
        }

    persona = LABEL_MAP.get(str(label), "desconocido")

    return {
        "accion": "abrir",
        "resultado": "autorizado",
        "persona": persona,
        "confianza": float(confidence)
    }

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    eventos = cargar_eventos()

    html = """
    <html>
    <head>
        <title>Historial de accesos</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f4f4f4;
            }
            .topbar {
                margin-bottom: 20px;
                padding: 15px;
                background: white;
                border-radius: 10px;
            }
            .evento {
                background: white;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            img {
                max-width: 320px;
                border-radius: 8px;
                margin-top: 10px;
            }
            .autorizado {
                color: green;
                font-weight: bold;
            }
            .rechazado {
                color: red;
                font-weight: bold;
            }
            .neutral {
                color: #555;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="topbar">
            <h1>Historial de accesos de la caja</h1>
            <p>Reconocimiento facial automatico activo</p>
        </div>
    """

    if not eventos:
        html += "<p>No hay eventos registrados todavía.</p>"
    else:
        for evento in eventos:
            if evento["resultado"] == "autorizado":
                clase = "autorizado"
            elif evento["resultado"] == "intento_fallido":
                clase = "rechazado"
            else:
                clase = "neutral"

            html += f"""
            <div class="evento">
                <p><b>Fecha:</b> {evento["timestamp"]}</p>
                <p><b>Archivo:</b> {evento["filename"]}</p>
                <p><b>Acción enviada al dispositivo:</b> {evento["accion"]}</p>
                <p><b>Resultado:</b> <span class="{clase}">{evento["resultado"]}</span></p>
                <p><b>Persona reconocida:</b> {evento.get("persona", "desconocido")}</p>
                <p><b>Confianza:</b> {evento.get("confianza", "N/A")}</p>
                <p><b>IP origen:</b> {evento["ip_origen"]}</p>
                <img src="/imagen/{evento['filename']}" alt="captura">
            </div>
            """

    html += """
    </body>
    </html>
    """
    return html

@app.route("/imagen/<filename>")
def ver_imagen(filename):
    return send_from_directory(SAVE_DIR, filename)

@app.route("/eventos")
def ver_eventos():
    return jsonify(cargar_eventos())

@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_data()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No se recibió imagen",
                "accion": "rechazar"
            }), 400

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"foto_{timestamp}.jpg"
        filepath = os.path.join(SAVE_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(data)

        decision = reconocer_persona(filepath)

        registrar_evento(
            filename=filename,
            accion=decision["accion"],
            ip_origen=request.remote_addr,
            resultado=decision["resultado"],
            persona=decision["persona"],
            confianza=decision["confianza"]
        )

        return jsonify({
            "status": "ok",
            "message": "Imagen recibida",
            "filename": filename,
            "accion": decision["accion"],
            "resultado": decision["resultado"],
            "persona": decision["persona"],
            "confianza": decision["confianza"]
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "accion": "rechazar"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)