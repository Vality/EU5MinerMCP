"""Small serializer helpers for the placeholder server."""


def serialize_status_message(message: str) -> dict[str, str]:
    return {"status": message}
