import requests

RESEND_API_KEY = "re_XWgCF8mt_NjYVjVhK3PXSvEaQRGPLN9mW"
TO_EMAIL = "sabes11343388@gmail.com"

payload = {
    "from": "onboarding@resend.dev",
    "to": [TO_EMAIL],
    "subject": "Prueba Resend",
    "html": "<p>Prueba correcta desde Render/Local</p>"
}

headers = {
    "Authorization": f"Bearer {RESEND_API_KEY}",
    "Content-Type": "application/json"
}

resp = requests.post(
    "https://api.resend.com/emails",
    headers=headers,
    json=payload,
    timeout=20
)

print(resp.status_code)
print(resp.text)