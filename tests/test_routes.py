import pytest
from opensearchpy import NotFoundError

from elasticsearch_client import es
from settings import get_settings
from tests.utils import populate_test_db

settings = get_settings()

def test_read_songs(client, test_session):
    populate_test_db(test_session, num_songs=2)

    response = client.get("/songs")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_read_songs_artists_param_transfer(client, test_session):
    songs = populate_test_db(test_session, num_songs=4)
    query_string = f"?artists={songs[0].artist_id},{songs[1].artist_id}"
    response = client.get("/songs/" + query_string)
    assert response.status_code == 200
    assert len(response.json()) == 2

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
    assert response.status_code == 204
    # Trying to get deleted elements
    response = client.get(f"/songs/{songs[0].id}")
    assert response.status_code == 404
    response = client.get(f"/songs/{songs[1].id}")
    assert response.status_code == 404

def test_delete_song_es_index(client, test_session):
    songs = populate_test_db(test_session, num_songs=4)

    client.request(
        method="DELETE",
        url="/songs",
        headers={"Content-Type": "application/json"},
        json={"song_ids": [songs[0].id, songs[1].id]}
    )

    for song_id in [songs[0].id, songs[1].id]:
        with pytest.raises(NotFoundError):
            es.get(index=settings.ES_SONG_INDEX_NAME, id=str(song_id))

def test_update_song(client, test_session):
    songs = populate_test_db(test_session, num_songs=2)

    payload = {"title": "New Title", "artist_id": songs[1].artist_id}
    response = client.put(f"/songs/{songs[0].id}", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["title"] == "New Title"
    assert data["artist"]["name"] == songs[1].artist.name

def test_update_song_es_index(client, test_session):
    songs = populate_test_db(test_session, num_songs=2)

    first_line, second_line = "New line 1", "New line 2"
    payload = {"title": "New Title", "artist_id": songs[1].artist_id, "lyrics": f"{first_line}\n{second_line}"}
    client.put(f"/songs/{songs[0].id}", json=payload)

    es_doc = es.get(index=settings.ES_SONG_INDEX_NAME, id=str(songs[0].id))
    assert es_doc["found"] is True
    assert "New Title" in es_doc["_source"]["title"]
    assert songs[1].artist.name in es_doc["_source"]["artist"]
    assert f"{first_line} {second_line}" in es_doc["_source"]["lines"]

def test_create_song(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)
    payload = {"title": "New Title", "artist_id": songs[0].artist_id, "lyrics": "Lyrics"}
    response = client.post("/songs", json=payload)
    assert response.status_code == 200
    assert "id" in response.json()

    # get created song
    song_id = response.json()["id"]
    response = client.get(f"/songs/{song_id}")
    assert response.status_code == 200

def test_create_song_with_lack_of_input(client):
    payload = {"title": "New Title", "lyrics": "Lyrics"}
    response = client.post("/songs", json=payload)
    assert response.status_code == 422

def test_create_song_with_incorrect_artist_input(client):
    payload = {"title": "New Title", "artist": "Artist name, not ID", "lyrics": "Lyrics"}
    response = client.post("/songs", json=payload)
    assert response.status_code == 422

def test_with_non_existing_artist(client):
    payload = {"title": "New Title", "artist_id": 999, "lyrics": "Lyrics"}
    response = client.post("/songs", json=payload)
    assert response.status_code == 404
    assert response.json()['detail'] == "Artist with given ID does not exist"

def test_create_song_es_index(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)
    payload = {"title": "New Title", "artist_id": songs[0].artist_id, "lyrics": "Lyrics"}
    response = client.post("/songs", json=payload)
    song_id = response.json()["id"]
    es.indices.refresh(index=settings.ES_SONG_INDEX_NAME)

    # Query ES to check that song was indexed
    es_doc = es.get(index=settings.ES_SONG_INDEX_NAME, id=str(song_id))
    assert es_doc["found"] is True

    # Check ES document contents
    assert response.json()["title"] in es_doc["_source"]["title"]
    assert response.json()["artist"]["name"] in es_doc["_source"]["artist"]

def test_export_to_pdf(client, test_session):
    songs = populate_test_db(test_session, num_songs=2)
    response = client.post("/songs/to_pdf", json={"song_ids": [songs[0].id, songs[1].id]})
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF"), "Response does not look like a valid PDF file"
    assert "Content-Disposition" in response.headers
    assert "filename=streamed.pdf" in response.headers["Content-Disposition"]

def test_read_artists(client, test_session):
    populate_test_db(test_session, num_songs=2)

    response = client.get("/artists")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_artist_by_id(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)

    response = client.get(f"/artists/{songs[0].artist_id}")
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == songs[0].artist_id

def test_create_artist(client):
    payload = {"name": "New Artist"}
    response = client.post("/artists", json=payload)
    assert response.status_code == 200
    assert "id" in response.json()

    # get created artist
    artist_id = response.json()["id"]
    response = client.get(f"/artists/{artist_id}")
    assert response.status_code == 200

def test_create_artist_already_exists(client):
    artist_name = "New Artist"
    payload = {"name": artist_name}
    client.post("/artists", json=payload)

    # try to create same artist
    response = client.post("/artists", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == f"Artist with name '{artist_name}' already exists"

def test_delete_artist(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)

    response = client.delete(f"/artists/{songs[0].artist_id}")

    assert response.status_code == 204
    # Trying to get deleted elements
    response = client.get(f"/artists/{songs[0].id}")
    assert response.status_code == 404

def test_delete_artist_not_found(client, test_session):
    response = client.delete(f"/artists/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Artist with ID 999 not found"

def test_update_artist(client, test_session):
    songs = populate_test_db(test_session, num_songs=1)

    new_artist_name = "New Artist"
    payload = {"name": new_artist_name}
    response = client.put(f"/artists/{songs[0].artist_id}", json=payload)
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == songs[0].artist_id
    assert data["name"] == new_artist_name

def test_update_artist_not_found(client, test_session):
    new_artist_name = "New Artist"
    payload = {"name": new_artist_name}
    response = client.put(f"/artists/999", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Artist with ID 999 not found"
