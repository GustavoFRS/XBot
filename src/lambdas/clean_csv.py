import os
import json
import boto3
import pandas as pd
from io import BytesIO, StringIO
from services.clean_csv_service import clean_csv

s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET_NAME")

def lambda_handler(event, context):
    """
    Handler da Lambda que lê o CSV bruto do S3, limpa e salva o resultado em outra pasta.
    Também retorna as linhas limpas (como JSON) para a próxima Lambda.
    """
    try:
        bucket = event["bucket"]
        key = event["key"]
        caminho_local = "/tmp/proposicoes_raw.csv"

        # 📥 Baixa o CSV original do S3
        s3.download_file(bucket, key, caminho_local)

        # 🧹 Limpa o arquivo com o service existente
        df_hoje = clean_csv(caminho_local)

        # 📤 Salva o arquivo limpo no S3
        output_key = key.replace("raw/", "clean/").replace(".csv", "_clean.csv")
        buffer = StringIO()
        df_hoje.to_csv(buffer, index=False)
        s3.put_object(Bucket=BUCKET, Key=output_key, Body=buffer.getvalue().encode("utf-8"))

        print(f"✅ CSV limpo salvo em s3://{BUCKET}/{output_key}")

        # Converte linhas do DataFrame em lista de dicionários (para passar no evento)
        linhas = df_hoje.to_dict(orient="records")

        return {
            "bucket": BUCKET,
            "key": output_key,
            "propositions": linhas
        }

    except Exception as e:
        print(f"❌ Erro no handler clean_csv: {e}")
        raise e
