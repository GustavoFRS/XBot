import requests
import logging
import json
from datetime import datetime, timezone

def get_bluesky_session(BLUESKY_HANDLE: str, BLUESKY_APP_PASSWORD: str):
    resp = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
    )
    resp.raise_for_status()
    session = resp.json()
    return session


# 🐦 Função de postagem agora recebe as credenciais e as repassa
def bluesky_post(credentials: dict, content: str):
    """Publica um tweet na API do X usando as credenciais fornecidas."""
    try:
        #session = get_bluesky_session(credentials["BLUESKY_HANDLE"], credentials["BLUESKY_APP_PASSWORD"])
        session = get_bluesky_session("botdacamara.bsky.social", "GYQAyHKUfG5ZpLC")
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        # Required fields that each post must include
        post = {
            "$type": "app.bsky.feed.post",
            "text": content,
            "createdAt": now,
        }

        resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"]},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )
        print(json.dumps(resp.json(), indent=2))
        resp.raise_for_status()

    except Exception as e:
        logging.error(f"❌ Falha ao postar o tweet. Erro da API: {e}")
        raise