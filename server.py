from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
import os
import json
from datetime import datetime

app = Flask(__name__)

SAVE_DIR = "recibidas"
EVENTS_FILE = "eventos.json"

os.makedirs(SAVE_DIR, exist_ok=True)

# Modo de prueba:
# "abrir" -> autorizado
# "rechazar" -> intento fallido
MODO_ACCION = {"valor": "abrir"}

def cargar_eventos():
    if not os.path.exists(EVENTS_FILE):
        return []

    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def guardar_eventos(eventos):
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)

def registrar_evento(filename, accion, ip_origen):
    eventos = cargar_eventos()

    if accion == "abrir":
        resultado = "autorizado"
    else:
        resultado = "intento_fallido"

    evento = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename,
        "accion": accion,
        "resultado": resultado,
        "ip_origen": ip_origen
    }

    eventos.insert(0, evento)
    guardar_eventos(eventos)

@app.route("/")
def index():
    eventos = cargar_eventos()

    html = f"""
    <html>
    <head>
        <title>Historial de accesos</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f4f4f4;
            }}
            .topbar {{
                margin-bottom: 20px;
                padding: 15px;
                background: white;
                border-radius: 10px;
            }}
            .evento {{
                background: white;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            img {{
                max-width: 320px;
                border-radius: 8px;
                margin-top: 10px;
            }}
            .autorizado {{
                color: green;
                font-weight: bold;
            }}
            .rechazado {{
                color: red;
                font-weight: bold;
            }}
            .boton {{
                display: inline-block;
                padding: 10px 14px;
                margin-right: 10px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 6px;
            }}
        </style>
    </head>
    <body>
        <div class="topbar">
            <h1>Historial de accesos de la caja</h1>
            <p><b>Modo actual del servidor:</b> {MODO_ACCION["valor"]}</p>
            <a class="boton" href="/modo/abrir">Modo abrir</a>
            <a class="boton" href="/modo/rechazar">Modo rechazar</a>
        </div>
    """

    if not eventos:
        html += "<p>No hay eventos registrados todavía.</p>"
    else:
        for evento in eventos:
            clase = "autorizado" if evento["resultado"] == "autorizado" else "rechazado"

            html += f"""
            <div class="evento">
                <p><b>Fecha:</b> {evento["timestamp"]}</p>
                <p><b>Archivo:</b> {evento["filename"]}</p>
                <p><b>Acción enviada al dispositivo:</b> {evento["accion"]}</p>
                <p><b>Resultado:</b> <span class="{clase}">{evento["resultado"]}</span></p>
                <p><b>IP origen:</b> {evento["ip_origen"]}</p>
                <img src="/imagen/{evento['filename']}" alt="captura">
            </div>
            """

    html += """
    </body>
    </html>
    """
    return html

@app.route("/modo/<accion>")
def cambiar_modo(accion):
    if accion in ["abrir", "rechazar"]:
        MODO_ACCION["valor"] = accion
    return redirect(url_for("index"))

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

        accion = MODO_ACCION["valor"]

        registrar_evento(
            filename=filename,
            accion=accion,
            ip_origen=request.remote_addr
        )

        print(f"[OK] Imagen guardada en: {filepath}")
        print(f"[OK] Evento registrado como: {accion}")

        return jsonify({
            "status": "ok",
            "message": "Imagen recibida",
            "filename": filename,
            "accion": accion
        }), 200

    except Exception as e:
        print("[ERROR]", e)
        return jsonify({
            "status": "error",
            "message": str(e),
            "accion": "rechazar"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)