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

def format_posts(json_content: dict):
    root_post = f"{json_content['numero']}\n {json_content['autor']} ({json_content['partido']})"
    reply_one = f"{json_content['ementa_resumida']}"
    points_text = "\n".join([f"- {p}" for p in json_content["pontos_chave"]])
    reply_two = "Resumo: \n" + points_text
    reply_three = f"Justificativa: {json_content['justificativa']} \n {json_content['link']}"

    return {
        'root_post': root_post,
        'reply_one': reply_one,
        'reply_two': reply_two,
        'reply_three': reply_three
    }

def reply_payload(content: str, root_uri: str, root_cid: str, parent_uri: str, parent_cid: str):
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "$type": "app.bsky.feed.post",
        "text": content,
        "createdAt": now,
        "reply": {
            "root": {
            "uri": root_uri,
            "cid": root_cid
            },
            "parent": {
            "uri": parent_uri,
            "cid": parent_cid
            }
        }
    }

# 🐦 Função de postagem agora recebe as credenciais e as repassa
def create_bluesky_post(credentials: dict, content: dict):
    """
    Publica um tweet na API do X usando as credenciais fornecidas.
    Return format:
    {
        "uri": "string",
        "cid": "string"
    }
    
    """
    try:
        #session = get_bluesky_session(credentials["BLUESKY_HANDLE"], credentials["BLUESKY_APP_PASSWORD"])
        session = get_bluesky_session("botdacamara.bsky.social", "GYQAyHKUfG5ZpLC")
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        formatted_posts = format_posts(content)

        # Root post
        post = {
            "$type": "app.bsky.feed.post",
            "text": formatted_posts['root_post'],
            "createdAt": now,
        }

        res = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"]},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )

        root_uri = res.json()["uri"]
        root_cid = res.json()["cid"]
        # Reply one
        post = reply_payload(formatted_posts['reply_one'], root_uri, root_cid, root_uri, root_cid)
        res = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"]},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )
        parent_uri = res.json()["uri"]
        parent_cid = res.json()["cid"]
        # Reply two
        post = reply_payload(formatted_posts['reply_two'], root_uri, root_cid, parent_uri, parent_cid)
        res = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"]},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )
        parent_uri = res.json()["uri"]
        parent_cid = res.json()["cid"]
        # Reply three
        post = reply_payload(formatted_posts['reply_three'], root_uri, root_cid, parent_uri, parent_cid)
        res = requests.post(
            "https://bsky.social/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"]},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )
        
        res.raise_for_status()
        return res.json()

    except Exception as e:
        logging.error(f"❌ Falha ao postar o tweet. Erro da API: {e}")
        raise


def create_x_post(credentials: dict, content: dict):
    pass