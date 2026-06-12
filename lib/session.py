import os

from itsdangerous import URLSafeTimedSerializer

TTL = 3600


def _ser() -> URLSafeTimedSerializer:
    key = os.environ.get("SESSION_SECRET", "local-dev-secret-change-me")
    return URLSafeTimedSerializer(key, salt="keystroke-round")


def seal(data: dict) -> str:
    return _ser().dumps(data)


def open(token: str) -> dict:
    return _ser().loads(token, max_age=TTL)
