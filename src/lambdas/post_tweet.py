import os
import boto3
import json
import logging
import tweepy
from services.post_tweet_service import create_bluesky_post
from datetime import datetime, timezone

print(datetime.now(timezone.utc))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

secrets_manager_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
X_SECRET_NAME = os.getenv("X_SECRET_NAME")

def get_x_credentials() -> dict:
    """Busca as credenciais do X no Secrets Manager e retorna como um dicionário."""
    try:
        response = secrets_manager_client.get_secret_value(SecretId=X_SECRET_NAME)
        secrets = json.loads(response['SecretString'])
        logger.info("Credenciais do X obtidas do Secrets Manager com sucesso.")
        return secrets
    except Exception as e:
        logger.error(f"Erro ao obter credenciais do X do Secrets Manager: {e}")
        raise


def lambda_handler(event, context):
    try:
        # 1. Obter as dependências (credenciais e conteúdo)
        credentials = get_x_credentials()
        s3_key = event.get("s3_key")
        
        if not s3_key:
            raise ValueError("O evento não contém a chave 's3_key'.")
            
        s3_object = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        post_data_json = json.loads(s3_object['Body'].read().decode('utf-8'))
        
        # 2. Injetar as dependências no serviço
        result = create_bluesky_post(
            credentials=credentials, 
            content=post_data_json
        )
        
        logger.info(f"Postagem finalizada com resultado: {result}")
        return {"statusCode": 200, "body": json.dumps(result)}

    except Exception as e:
        logger.error(f"ERRO GERAL NO HANDLER: {e}")
        raise e