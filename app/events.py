import json
from datetime import datetime
from pathlib import Path
from threading import Lock


_event_lock = Lock()


def read_events(events_file: Path) -> list[dict]:
    """Lee el historial de eventos."""

    if not events_file.exists():
        return []

    try:
        with events_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (json.JSONDecodeError, OSError):
        return []


def add_event(
    events_file: Path,
    filename: str,
    accion: str,
    ip_origen: str | None,
    resultado: str,
    persona: str,
    confianza: float | None,
) -> dict:
    """Registra un nuevo intento de acceso."""

    events_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    event = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "filename": filename,
        "accion": accion,
        "resultado": resultado,
        "persona": persona,
        "confianza": confianza,
        "ip_origen": ip_origen,
    }

    with _event_lock:
        events = read_events(events_file)

        # Mantiene el evento más reciente al inicio.
        events.insert(0, event)

        temporary_file = events_file.with_suffix(".tmp")

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                events,
                file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_file.replace(events_file)

    return event