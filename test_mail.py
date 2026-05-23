import smtplib
from email.message import EmailMessage

MAIL_SENDER = "sabes11343388@gmail.com"
MAIL_PASSWORD = "gufzvhikwfvkwwjo"
MAIL_RECIPIENT = "sisaspelele17@gmail.com"
MAIL_SMTP_HOST = "smtp.gmail.com"
MAIL_SMTP_PORT = 465

msg = EmailMessage()
msg["Subject"] = "Prueba correo caja fuerte"
msg["From"] = MAIL_SENDER
msg["To"] = MAIL_RECIPIENT
msg.set_content("Esto es una prueba de envio de correo desde Python.")

with smtplib.SMTP_SSL(MAIL_SMTP_HOST, MAIL_SMTP_PORT, timeout=20) as smtp:
    smtp.login(MAIL_SENDER, MAIL_PASSWORD)
    smtp.send_message(msg)

print("Correo enviado correctamente")