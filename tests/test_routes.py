import pytest

from tests.utils import populate_test_db


def test_read_songs(client, test_session):
    populate_test_db(test_session, num_songs=2)

    response = client.get("/songs")
    assert response.status_code == 200
    assert len(response.json()) == 2

@pytest.mark.skip(reason="Need to fix this. Mock elasticsearch")
def test_read_songs_with_search(client, test_session):
    songs = populate_test_db(test_session, num_songs=2)

    response = client.get("/songs", params={"search": songs[0].title})
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_song_by_id(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)

    response = client.get(f"/songs/{songs[0].id}")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == songs[0].id

def test_delete_song(client, test_session):
    songs = populate_test_db(test_session, num_songs=4)

    response = client.request(
        method="DELETE",
        url="/songs",
        headers={"Content-Type": "application/json"},
        json={"song_ids": [songs[0].id, songs[1].id]}
    )
    assert response.status_code == 200
    # Trying to get deleted elements
    response = client.get(f"/songs/{songs[0].id}")
    assert response.status_code == 404
    response = client.get(f"/songs/{songs[1].id}")
    assert response.status_code == 404

def test_update_song(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)

    payload = {"title": "New Title", "artist": "New Artist"}
    response = client.put(f"/songs/{songs[0].id}", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["title"] == "New Title"
    assert data["artist"] == "New Artist"

def test_create_song(client):
    payload = {"title": "New Title", "artist": "New Artist", "lyrics": "Lyrics"}
    response = client.post("/songs", json=payload)
    assert response.status_code == 200
    assert "id" in response.json()

    # get created song
    song_id = response.json()["id"]
    response = client.get(f"/songs/{song_id}")
    assert response.status_code == 200

def test_create_song_with_improper_input(client):
    payload = {"title": "New Title", "artist": "New Artist"}
    response = client.post("/songs", json=payload)
    assert response.status_code == 422

def test_export_to_pdf(client, test_session):
    songs = populate_test_db(test_session, num_songs=2)
    response = client.post("/songs/to_pdf", json={"song_ids": [songs[0].id, songs[1].id]})
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF"), "Response does not look like a valid PDF file"
    assert "Content-Disposition" in response.headers
    assert "filename=streamed.pdf" in response.headers["Content-Disposition"]
