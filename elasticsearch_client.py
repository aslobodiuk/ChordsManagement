from elasticsearch import Elasticsearch

from models.db_models import Song
from settings import settings

es = Elasticsearch(settings.ELASTICSEARCH_URL)

def index_song(song: Song):
    """
    Index a song in Elasticsearch using its ID.
    `song` should be an instance of your Song model, with related lines loaded.
    """
    doc = {
        "title": song.title,
        "artist": song.artist,
        "lines": " ".join([line.text for line in song.lines])
    }
    es.index(index="songs", id=str(song.id), document=doc)

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

    response = es.search(index="songs", body=body)

    results = []
    for hit in response["hits"]["hits"]:
        results.append({
            "id": hit["_id"],
            "score": hit["_score"],
            "highlight": hit.get("highlight", {})
        })

    return results

