import os
import boto3
import json
from services.generate_tweet_service import gerar_resumo

# CLients
s3_client = boto3.client("s3")
secrets_manager_client = boto3.client("secretsmanager")
# Variables
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
SECRET_NAME = os.getenv("OPENAI_API_KEY")

def get_openai_key() -> str:
    """Busca a chave da API do Secrets Manager."""
    try:
        response = secrets_manager_client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response['SecretString'])
        return secret['OPENAI_API_KEY']
    except Exception as e:
        print(f"Erro ao buscar o segredo '{SECRET_NAME}': {e}")
        raise


def lambda_handler(event, context):
    """
    Lambda handler para gerar um tweet para uma única proposição.
    """
    print(f"Recebido evento para processamento: {event}")

    # Extrai informações da proposição vinda do estado Map
    proposition_key = event.get('inteiro_teor_key')
    if not proposition_key:
        msg = "Chave 'inteiro_teor_key' não encontrada no evento."
        print(msg)
        return {
            "statusCode": 400,
            "error": msg,
            "event": event
        }

    try:
        # 1. Lê o texto da proposição do S3
        s3_object = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=proposition_key)
        full_text = s3_object['Body'].read().decode('utf-8')

        # 2. Chama a função para gerar o tweet
        post_data_json = gerar_resumo(
            api_key=get_openai_key(),
            text=full_text,
            numero_pec=event['Proposições'],
            autor=event['Autor'],
            partido=event['Partido'],
            uf=event['UF'],
            ementa=event['Ementa'],
            link=event['Link']
        )
        
        print(f"JSON gerado com sucesso para {event['Proposições']}")
        # 3 Salvar tweet em s3
        post_data_key = proposition_key.replace("/inteiro_teor.txt", "/post_data.json")

        s3_client.put_object(
            Bucket=S3_BUCKET_NAME, 
            Key=post_data_key, 
            Body=json.dumps(post_data_json, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType="application/json"
        )

        print(f"JSON salvo em s3://{S3_BUCKET_NAME}/{post_data_key}")


        # 4. Retorna o resultado
        return {
            "statusCode": 200,
            "proposition": event['Proposições'],
            "tweet_key": post_data_key
        }

    except Exception as e:
        print(f"Erro ao processar {event.get('Proposições', 'proposição desconhecida')}: {str(e)}")
        # Retorna o erro para que a Step Function possa lidar com ele
        raise e