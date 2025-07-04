import json


def print_payload_for_postman(lyrics):
    print(json.dumps({"lyrics": lyrics}, ensure_ascii=False, indent=2))