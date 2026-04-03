from app import create_app

def test_example():
    app = create_app()
    client = app.test_client()

    response = client.get("/users")

    assert response.status_code == 200