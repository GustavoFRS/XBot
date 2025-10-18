import os
import json
import boto3
from services.fetch_projects_csv_service import fetch_projects_csv

s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET_NAME")

def lambda_handler(event, context):
    """
    Handler da Lambda responsável por baixar o CSV da Câmara e salvar no S3.
    """
    try:
        caminho_local = "/tmp/proposicoes.csv"

        # 📥 Chama o service para baixar o CSV localmente
        fetch_projects_csv(caminho_arquivo=caminho_local)

        # 🔼 Envia para o S3
        s3_key = f"data/raw/proposicoes.csv"
        s3.upload_file(caminho_local, BUCKET, s3_key)

        print(f"✅ CSV salvo em s3://{BUCKET}/{s3_key}")

        # Retorna para o próximo passo da Step Function
        return {
            "bucket": BUCKET,
            "key": s3_key,
        }

    except Exception as e:
        print(f"❌ Erro no handler download_csv: {e}")
        raise e