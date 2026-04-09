from src.adapters.storage import load_transcript, save_transcript


def test_save_transcript_writes_json_payload(tmp_path) -> None:
    path = tmp_path / "transcript.json"
    payload = {
        "video_id": "abc123",
        "transcript": "Clean transcript",
        "status": "available",
    }

    save_transcript(str(path), payload)

    assert path.exists()
    assert path.read_text(encoding="utf-8") == (
        '{\n'
        '  "video_id": "abc123",\n'
        '  "transcript": "Clean transcript",\n'
        '  "status": "available"\n'
        '}'
    )


def test_load_transcript_reads_json_payload(tmp_path) -> None:
    path = tmp_path / "transcript.json"
    path.write_text(
        '{\n'
        '  "video_id": "missing-video",\n'
        '  "transcript": "",\n'
        '  "status": "missing"\n'
        '}',
        encoding="utf-8",
    )

    payload = load_transcript(str(path))

    assert payload == {
        "video_id": "missing-video",
        "transcript": "",
        "status": "missing",
    }
