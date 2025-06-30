from opensearchpy import OpenSearch

from models.db_models import Song
from settings import settings

es = OpenSearch(settings.ELASTICSEARCH_URL)

def create_songs_index_if_needed():
    """
    Create the 'songs' index in OpenSearch if it doesn't exist.
    Can include mapping if needed.
    """
    if not es.indices.exists(index="songs"):
        es.indices.create(index="songs", body={
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "artist": {"type": "text"},
                    "lines": {"type": "text"}
                }
            }
        })

def index_song(song: Song):
    """
    Index a song in OpenSearch using its ID.
    `song` should be an instance of your Song model, with related lines loaded.
    """
    doc = {
        "title": song.title,
        "artist": song.artist,
        "lines": " ".join([line.text for line in song.lines])
    }
    es.index(index="songs", id=str(song.id), body=doc)

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

