import os
import uuid
import boto3
from slugify import slugify
from services.fetch_individual_project_service import fetch_individual_project

s3 = boto3.client("s3")
BUCKET = os.getenv("S3_BUCKET_NAME")

def lambda_handler(event, context):
    """
    Itera sobre proposições, salva page.html e inteiro_teor.txt no S3
    e adiciona o campo 'inteiro_teor_key' a cada proposição.
    Recebe: {
            "bucket": BUCKET,
            "key": output_key,
            "propositions": linhas
        }
    """
    try:
        # Acessa o dicionário 'cleanCsv' primeiro
        clean_csv_output = event.get("cleanCsv", {})
        
        # Agora, extrai as variáveis de dentro desse dicionário
        bucket = clean_csv_output.get("bucket", BUCKET)
        propositions = clean_csv_output.get("propositions", [])

        if not propositions:
            print("⚠️ Nenhuma proposição recebida para processar.")
            return {"bucket": bucket, "propositions": []}

        print(f"📦 Processando {len(propositions)} proposições...")

        for idx, prop in enumerate(propositions, start=1):
            nome = slugify(prop.get("Proposições", f"desconhecida_{uuid.uuid4()}"))

            try:
                print(f"({idx}/{len(propositions)}) ▶️ {nome}")
                resultado = fetch_individual_project(prop)

                html_content = resultado.get("html")
                texto = resultado.get("texto")

                # 🔹 Salvar HTML sempre
                if html_content:
                    html_key = f"propositions/{nome}/page.html"
                    s3.put_object(
                        Bucket=bucket,
                        Key=html_key,
                        Body=html_content.encode("utf-8"),
                        ContentType="text/html"
                    )
                else:
                    html_key = None

                # 🔹 Salvar texto apenas se existir
                if texto:
                    txt_key = f"propositions/{nome}/inteiro_teor.txt"
                    s3.put_object(
                        Bucket=bucket,
                        Key=txt_key,
                        Body=texto.encode("utf-8"),
                        ContentType="text/plain"
                    )
                    prop["inteiro_teor_key"] = txt_key
                    print(f"✅ Texto salvo em s3://{bucket}/{txt_key}")
                else:
                    prop["inteiro_teor_key"] = None

            except Exception as e:
                print(f"❌ Erro ao processar {nome}: {e}")
                prop["inteiro_teor_key"] = None

        # ✅ Retorna a mesma lista, mas enriquecida
        # TODO: CORRIGIR SAIDA
        return {
            "bucket": bucket,
            "propositions": propositions
            }

    except Exception as e:
        print(f"❌ Erro no handler fetch_individual_project: {e}")
        raise