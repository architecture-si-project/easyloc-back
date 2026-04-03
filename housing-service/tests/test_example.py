from app import create_app

def test_example():
    app = create_app()
    houses = app.test_client()

    response = houses.get("/houses")

    assert response.status_code == 200