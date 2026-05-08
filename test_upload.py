import requests

url = "http://127.0.0.1:5000/upload"
archivo = "julian.jpg"   # cambia esto por una imagen de prueba

with open(archivo, "rb") as f:
    r = requests.post(url, data=f.read())

print("Status code:", r.status_code)
print("Respuesta:")
print(r.text)