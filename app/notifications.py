import requests


def send_event_notification(
    event: dict,
    api_key: str,
    sender: str,
    recipient: str,
    public_base_url: str,
) -> bool:
    """Envía por correo la información de un intento de acceso."""

    if not api_key or not recipient:
        return False

    image_url = (
        f"{public_base_url}/imagen/{event['filename']}"
    )

    dashboard_url = f"{public_base_url}/"

    subject = (
        f"[Caja fuerte] "
        f"{event['resultado']} - "
        f"{event['persona']}"
    )

    html = f"""
    <h2>Nuevo intento de acceso</h2>
    <p><b>Fecha:</b> {event['timestamp']}</p>
    <p><b>Archivo:</b> {event['filename']}</p>
    <p><b>Acción:</b> {event['accion']}</p>
    <p><b>Resultado:</b> {event['resultado']}</p>
    <p><b>Persona:</b> {event['persona']}</p>
    <p><b>Confianza:</b> {event['confianza']}</p>
    <p><b>IP origen:</b> {event['ip_origen']}</p>
    <p><a href="{image_url}">Ver imagen capturada</a></p>
    <p><a href="{dashboard_url}">Ver historial completo</a></p>
    """

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "html": html,
        },
        timeout=20,
    )

    response.raise_for_status()

    return True