from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    request,
    send_from_directory,
)

from app.config import Config
from app.events import add_event, read_events
from app.notifications import send_event_notification
from app.recognition import FaceRecognizer


main = Blueprint(
    "main",
    __name__,
)


# El modelo se carga una sola vez cuando inicia la aplicación.
recognizer = FaceRecognizer(
    model_path=Config.MODEL_PATH,
    labels_path=Config.LABELS_PATH,
)


# Garantiza que exista la carpeta donde se guardan las imágenes.
Config.UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@main.route("/health")
def health():
    return jsonify({
        "status": "ok",
    })


@main.route("/eventos")
def ver_eventos():
    eventos = read_events(
        Config.EVENTS_FILE
    )

    return jsonify(eventos)


@main.route("/imagen/<filename>")
def ver_imagen(filename):
    return send_from_directory(
        Config.UPLOAD_DIR,
        filename,
    )


@main.route("/")
def index():
    eventos = read_events(
        Config.EVENTS_FILE
    )

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
        html += """
        <p>
            No hay eventos registrados todavía.
        </p>
        """

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
                <p>
                    <b>Fecha:</b>
                    {evento["timestamp"]}
                </p>

                <p>
                    <b>Archivo:</b>
                    {evento["filename"]}
                </p>

                <p>
                    <b>Acción enviada al dispositivo:</b>
                    {evento["accion"]}
                </p>

                <p>
                    <b>Resultado:</b>
                    <span class="{clase}">
                        {evento["resultado"]}
                    </span>
                </p>

                <p>
                    <b>Persona reconocida:</b>
                    {evento.get("persona", "desconocido")}
                </p>

                <p>
                    <b>Confianza:</b>
                    {evento.get("confianza", "N/A")}
                </p>

                <p>
                    <b>IP origen:</b>
                    {evento["ip_origen"]}
                </p>

                <img
                    src="/imagen/{evento['filename']}"
                    alt="captura"
                >
            </div>
            """

    html += """
    </body>
    </html>
    """

    return html


@main.route(
    "/upload",
    methods=["POST"],
)
def upload():
    try:
        data = request.get_data()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No se recibió imagen",
                "accion": "rechazar",
            }), 400

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"foto_{timestamp}.jpg"
        )

        filepath = (
            Config.UPLOAD_DIR
            / filename
        )

        with filepath.open(
            "wb"
        ) as file:
            file.write(data)

        decision = (
            recognizer.recognize_file(
                filepath
            )
        )

        evento = add_event(
            events_file=Config.EVENTS_FILE,
            filename=filename,
            accion=decision["accion"],
            ip_origen=request.remote_addr,
            resultado=decision["resultado"],
            persona=decision["persona"],
            confianza=decision["confianza"],
        )

        # Los accesos autorizados quedan registrados.
        # Las alertas por correo se envían
        # únicamente para intentos rechazados.
        if (
            decision["resultado"]
            != "autorizado"
        ):
            try:
                send_event_notification(
                    event=evento,
                    api_key=(
                        Config.RESEND_API_KEY
                    ),
                    sender=(
                        Config.RESEND_FROM
                    ),
                    recipient=(
                        Config.MAIL_RECIPIENT
                    ),
                    public_base_url=(
                        Config.PUBLIC_BASE_URL
                    ),
                )

            except Exception as error:
                print(
                    "Error enviando notificación:",
                    repr(error),
                )

        return jsonify({
            "status": "ok",
            "message": "Imagen recibida",
            "filename": filename,
            "accion": decision["accion"],
            "resultado": decision["resultado"],
            "persona": decision["persona"],
            "confianza": decision["confianza"],
        }), 200

    except Exception as error:
        return jsonify({
            "status": "error",
            "message": str(error),
            "accion": "rechazar",
        }), 500