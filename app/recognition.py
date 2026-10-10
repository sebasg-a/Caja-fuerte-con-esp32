import json
from pathlib import Path

import cv2


class FaceRecognizer:
    """Encapsula la detección y reconocimiento facial con OpenCV."""

    def __init__(
        self,
        model_path: Path,
        labels_path: Path,
    ):
        self.model_path = model_path
        self.labels_path = labels_path

        self.face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.read(str(self.model_path))

        with self.labels_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.labels = json.load(file)

    def recognize_file(self, filepath: Path) -> dict:
        """Reconoce una persona desde una imagen almacenada."""

        image = cv2.imread(str(filepath))

        if image is None:
            return {
                "accion": "rechazar",
                "resultado": "error_imagen",
                "persona": "desconocido",
                "confianza": None,
            }

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
        )

        if len(faces) == 0:
            return {
                "accion": "rechazar",
                "resultado": "sin_rostro",
                "persona": "desconocido",
                "confianza": None,
            }

        x, y, width, height = faces[0]

        face = gray[
            y : y + height,
            x : x + width,
        ]

        face = cv2.resize(
            face,
            (200, 200),
        )

        label, confidence = self.recognizer.predict(face)

        if label == -1:
            return {
                "accion": "rechazar",
                "resultado": "intento_fallido",
                "persona": "desconocido",
                "confianza": float(confidence),
            }

        person = self.labels.get(
            str(label),
            "desconocido",
        )

        return {
            "accion": "abrir",
            "resultado": "autorizado",
            "persona": person,
            "confianza": float(confidence),
        }