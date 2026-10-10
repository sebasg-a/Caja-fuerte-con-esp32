import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Configuración de la aplicación cargada desde variables de entorno."""

    PORT = int(
    os.getenv("PORT", "5000")
    )   

    UPLOAD_DIR = Path(
        os.getenv("UPLOAD_DIR", BASE_DIR / "recibidas")
    )

    EVENTS_FILE = Path(
        os.getenv("EVENTS_FILE", UPLOAD_DIR / "eventos.json")
    )

    MODEL_PATH = Path(
        os.getenv("MODEL_PATH", BASE_DIR / "model" / "lbph_model.yml")
    )

    LABELS_PATH = Path(
        os.getenv("LABELS_PATH", BASE_DIR / "model" / "labels.json")
    )

    FACE_THRESHOLD = float(
        os.getenv("FACE_THRESHOLD", "70.0")
    )

    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024))
    )

    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM = os.getenv(
        "RESEND_FROM",
        "onboarding@resend.dev"
    )
    MAIL_RECIPIENT = os.getenv("MAIL_RECIPIENT", "")

    PUBLIC_BASE_URL = os.getenv(
        "PUBLIC_BASE_URL",
        "http://localhost:5000"
    ).rstrip("/")