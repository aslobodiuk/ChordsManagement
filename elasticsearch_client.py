from opensearchpy import OpenSearch

from models.db_models import Song, Artist
from settings import get_settings

settings = get_settings()

es = OpenSearch(settings.ELASTICSEARCH_URL)

def index_song(song: Song):
    """
    Index a song in Elasticsearch using its ID.
    `song` should be an instance of your Song model, with related lines loaded.
    """
    doc = {
        "title": song.title,
        "artist": song.artist.name,
        "lines": " ".join([line.text for line in song.lines])
    }
    es.index(index=settings.ES_SONG_INDEX_NAME, id=str(song.id), body=doc)

def index_artist(artist: Artist):
    doc = {
        "name": artist.name,
        "songs": [song.title for song in artist.songs]
    }
    es.index(index=settings.ES_ARTIST_INDEX_NAME, id=str(artist.id), body=doc)

def search(index_name, body):
    """Search function"""
    response = es.search(index=index_name, body=body)

    results = []
    for hit in response["hits"]["hits"]:
        results.append({
            "id": hit["_id"],
            "score": hit["_score"],
            "highlight": hit.get("highlight", {})
        })

    return results

def search_songs(query: str, limit: int = 20):
    """
    Searches Elasticsearch by title, artist, or line text.
    Returns a list of matching song IDs and highlights
    """
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["title", "artist", "lines"],
                "fuzziness": "AUTO"
            }
        },
        "highlight": {
            "fields": {
                "title": {},
                "artist": {},
                "lines": {}
            }
        },
        "size": limit
    }

    return search(settings.ES_SONG_INDEX_NAME, body)

def search_artists(query: str, limit: int = 20):
    """
    Searches Elasticsearch by artist name and song titles.
    Returns a list of matching artist IDs and highlights
    """
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["name", "songs"],
                "fuzziness": "AUTO"
            }
        },
        "highlight": {
            "fields": {
                "name": {},
                "songs": {}
            }
        },
        "size": limit
    }
    return search(settings.ES_ARTIST_INDEX_NAME, body)

