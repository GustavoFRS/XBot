# src/lambdas/scheduler_lambda.py

import os
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from services.schedule_tweet_service import list_pending_tweets_for_date, create_schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Carrega as configurações do ambiente
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
POSTER_LAMBDA_ARN = os.getenv("POSTER_LAMBDA_ARN")
SCHEDULER_ROLE_ARN = os.getenv("SCHEDULER_ROLE_ARN")

def lambda_handler(event, context):
    """
    Handler invocado diariamente para encontrar e agendar tweets do dia anterior.
    """
    logger.info("SchedulerLambda iniciada.")
    
    # ... (validação das variáveis de ambiente) ...

    try:
        # 1. Obter a data e fuso horário local
        local_tz = ZoneInfo("America/Sao_Paulo")
        today_local = datetime.now(local_tz).date() 
        
        # 2. Calcular o início e o fim do dia de HOJE no fuso local
        start_of_today_local = datetime(
            today_local.year, today_local.month, today_local.day, tzinfo=local_tz
        )
        end_of_today_local = start_of_today_local + timedelta(days=1)

        # 3. Converter o intervalo para UTC para consultar o S3
        start_utc = start_of_today_local.astimezone(ZoneInfo("UTC"))
        end_utc = end_of_today_local.astimezone(ZoneInfo("UTC"))
        
        # 2. Encontrar tweets pendentes do dia anterior
        pending_tweets = list_pending_tweets_for_date(
            bucket_name=S3_BUCKET_NAME,
            start_utc=start_utc,
            end_utc=end_utc
        )

        if not pending_tweets:
            logger.info("Nenhum tweet novo para agendar. Finalizando.")
            return {"status": "success", "message": "No new tweets to schedule."}

        # 3. Definir o horário de início dos posts (ex: hoje a partir das 09:00 BRT / 12:00 UTC)
        now_local = datetime.now(local_tz)
        
        # O horário de início será daqui a 2 minutos para garantir que está no futuro
        start_time_local = now_local + timedelta(minutes=2)
        logger.info(f"Hora atual: {now_local.isoformat()}. O primeiro agendamento começará a partir de {start_time_local.isoformat()}")
        
        # 4. Chamar o serviço para criar os agendamentos
        result = create_schedules(
            tweet_keys=pending_tweets,
            start_time=start_time_local,
            interval_minutes=3, # Postar a cada 60 minutos / TESTE: 3 MINUTOS
            poster_lambda_arn=POSTER_LAMBDA_ARN,
            scheduler_role_arn=SCHEDULER_ROLE_ARN
        )
        
        logger.info(f"Processo de agendamento finalizado: {result}")
        return {"status": "success", "body": result}

    except Exception as e:
        logger.error(f"Erro inesperado no handler do Scheduler: {e}")
        raise e