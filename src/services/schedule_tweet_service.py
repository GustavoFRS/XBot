import boto3
import json
import logging
from zoneinfo import ZoneInfo
from slugify import slugify
from datetime import datetime, timedelta, timezone, date

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

s3_client = boto3.client("s3")
scheduler_client = boto3.client("scheduler")

def list_pending_tweets_for_date(bucket_name: str, start_utc: datetime, end_utc: datetime) -> list[str]:
    """
    Lista os arquivos 'tweet.txt' em um bucket S3 que foram criados em uma data específica (UTC).

    Args:
        bucket_name (str): O nome do bucket S3.
        target_date (date): A data específica para buscar os arquivos.

    Returns:
        Uma lista de S3 keys para os tweets pendentes.
    """
    logger.info(f"Buscando tweets pendentes entre {start_utc.isoformat()} e {end_utc.isoformat()}")
    
    pending_tweets = []
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix="propositions/")

    for page in pages:
        for obj in page.get('Contents', []):
            if obj['Key'].endswith('tweet.txt') and start_utc <= obj['LastModified'] < end_utc:
                pending_tweets.append(obj['Key'])
                
    logger.info(f"Encontrados {len(pending_tweets)} tweets para agendar.")
    return pending_tweets


def create_schedules(
    tweet_keys: list[str],
    start_time: datetime, # Espera-se um datetime com fuso horário (aware)
    interval_minutes: int,
    poster_lambda_arn: str,
    scheduler_role_arn: str
) -> dict:
    """
    Cria agendamentos one-time no EventBridge Scheduler para uma lista de tweets.
    Garante que todos os horários são convertidos para UTC antes de agendar.
    """
    # Validação importante: garante que a função não receba datetimes "ingênuos"
    if start_time.tzinfo is None:
        raise ValueError("Erro: O start_time deve ter um fuso horário definido (timezone-aware).")

    logger.info(f"Criando {len(tweet_keys)} agendamentos, começando em {start_time.isoformat()} com intervalo de {interval_minutes} min.")
    
    schedules_created = 0
    current_schedule_time = start_time

    for key in tweet_keys:
        sanitized_key = slugify(key) # Supondo que você tenha a função slugify
        schedule_name = f"tweet-{sanitized_key}"

        # 1. Garante que o horário atual do loop esteja em UTC
        utc_schedule_time = current_schedule_time.astimezone(timezone.utc)
        
        # 2. Formata a string a partir do objeto UTC garantido
        schedule_time_str = utc_schedule_time.strftime('%Y-%m-%dT%H:%M:%S')
        # ---------------------

        try:
            scheduler_client.create_schedule(
                Name=schedule_name,
                GroupName='default',
                ScheduleExpression=f"at({schedule_time_str})",
                Target={
                    'Arn': poster_lambda_arn,
                    'RoleArn': scheduler_role_arn,
                    'Input': json.dumps({"s3_key": key})
                },
                FlexibleTimeWindow={'Mode': 'OFF'},
                ActionAfterCompletion='DELETE'
            )
            logger.info(f"Agendamento '{schedule_name}' criado para as {schedule_time_str} UTC.")
            schedules_created += 1
        except scheduler_client.exceptions.ConflictException:
            logger.warning(f"Agendamento '{schedule_name}' já existe. Ignorando.")
        except Exception as e:
            logger.error(f"Falha ao criar agendamento para a chave '{key}'. Erro: {e}")
            
        current_schedule_time += timedelta(minutes=interval_minutes)
        
    return {"schedules_created": schedules_created}