import os
import tweepy
import logging
import time
from dotenv import load_dotenv
from tweepy.errors import TooManyRequests, Forbidden, TweepyException

# Configuração de logging (útil tanto local quanto em Lambda)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Carrega .env automaticamente em ambiente local
load_dotenv()

# 🔐 Cria e retorna o cliente Tweepy
def get_x_client() -> tweepy.Client:
    try:
        client = tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_SECRET")
        )
        return client
    except Exception as e:
        logging.error(f"❌ Erro ao inicializar o cliente do X: {e}")
        raise


def post_tweet(text: str) -> bool:
    """
    Publica um tweet de forma segura.
    Retorna True se sucesso, False caso contrário.
    """

    client = get_x_client()

    try:
        if len(text) > 280:
            logging.warning(f"⚠️ Tweet com {len(text)} caracteres foi truncado.")
            text = text[:277] + "..."

        response = client.create_tweet(text=text)
        tweet_id = response.data.get("id")

        logging.info(f"✅ Tweet publicado com sucesso: https://x.com/i/web/status/{tweet_id}")
        return True

    except TooManyRequests as e:
        logging.error("🚫 Rate limit excedido. Esperando 15 minutos antes de tentar novamente.")
        time.sleep(900)  # 15 minutos
        return False

    except Forbidden as e:
        logging.error(f"❌ Erro de permissão (verifique permissões Read/Write): {e}")
        return False

    except TweepyException as e:
        logging.error(f"⚠️ Erro inesperado do Tweepy: {e}")
        return False

    except Exception as e:
        logging.error(f"❌ Falha inesperada ao postar tweet: {e}")
        return False
