def test_read_songs(client):
    response = client.get("/songs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["title"] == "Test Song"