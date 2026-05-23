from flask import Flask, request, jsonify, send_from_directory
import os
import json
import cv2
import requests
from datetime import datetime

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5000))
SAVE_DIR = os.environ.get("UPLOAD_DIR", "recibidas")
EVENTS_FILE = os.path.join(SAVE_DIR, "eventos.json")

MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "lbph_model.yml")
LABELS_PATH = os.path.join(MODEL_DIR, "labels.json")

# Resend / Email API
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "Caja Fuerte <notificaciones@tu-dominio.com>")
MAIL_RECIPIENT = os.environ.get("MAIL_RECIPIENT", "sisaspelele17@gmail.com")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://caja-fuerte-con-esp32.onrender.com")

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
    return evento


def enviar_correo_evento(evento):
    if not RESEND_API_KEY:
        print("Correo no configurado: falta RESEND_API_KEY")
        return

    image_url = f"{PUBLIC_BASE_URL}/imagen/{evento['filename']}"
    dashboard_url = f"{PUBLIC_BASE_URL}/"

    asunto = f"[Caja fuerte] {evento['resultado']} - {evento['persona']}"

    html = f"""
    <h2>Nuevo intento de acceso</h2>
    <p><b>Fecha:</b> {evento['timestamp']}</p>
    <p><b>Archivo:</b> {evento['filename']}</p>
    <p><b>Acción:</b> {evento['accion']}</p>
    <p><b>Resultado:</b> {evento['resultado']}</p>
    <p><b>Persona:</b> {evento['persona']}</p>
    <p><b>Confianza:</b> {evento['confianza']}</p>
    <p><b>IP origen:</b> {evento['ip_origen']}</p>
    <p><a href="{image_url}">Ver imagen capturada</a></p>
    <p><a href="{dashboard_url}">Ver historial completo</a></p>
    """

    payload = {
        "from": RESEND_FROM,
        "to": [MAIL_RECIPIENT],
        "subject": asunto,
        "html": html,
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        "https://api.resend.com/emails",
        headers=headers,
        json=payload,
        timeout=20,
    )

    if resp.status_code >= 300:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")

    print("Correo enviado via API HTTPS a:", MAIL_RECIPIENT)
    print("Respuesta Resend:", resp.text)


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
            <p>Reconocimiento facial automático activo</p>
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

        evento = registrar_evento(
            filename=filename,
            accion=decision["accion"],
            ip_origen=request.remote_addr,
            resultado=decision["resultado"],
            persona=decision["persona"],
            confianza=decision["confianza"]
        )

        try:
            enviar_correo_evento(evento)
        except Exception as e:
            print("Error enviando correo por API HTTPS:", repr(e))

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