import json


def save_transcript(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_transcript(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
