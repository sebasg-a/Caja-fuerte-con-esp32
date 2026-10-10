from app import create_app


def test_health():
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok"
    }


def test_eventos_without_data():
    app = create_app()
    client = app.test_client()

    response = client.get("/eventos")

    assert response.status_code == 200
    assert isinstance(
        response.get_json(),
        list,
    )


def test_upload_without_image():
    app = create_app()
    client = app.test_client()

    response = client.post(
        "/upload",
        data=b"",
        content_type="image/jpeg",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["accion"] == "rechazar"