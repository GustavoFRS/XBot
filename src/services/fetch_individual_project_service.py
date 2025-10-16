import requests
import boto3
from io import BytesIO
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_individual_project(url: str, bucket_s3: str = None):
    """
    Acessa a página de um projeto (PL/PEC), identifica o link do inteiro teor,
    baixa o PDF, extrai o texto e salva como .txt (local ou S3).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # 1️⃣ Acessar a página do projeto
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # 2️⃣ (Opcional) salvar HTML localmente para debug
    with open("proposicao_individual.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    # 3️⃣ Encontrar o link do inteiro teor (classe correta)
    link_inteiro_teor = soup.find("a", class_="linkDownloadTeor")
    if not link_inteiro_teor or not link_inteiro_teor.get("href"):
        print("❌ Não foi possível encontrar o link do inteiro teor.")
        return None

    pdf_url = link_inteiro_teor["href"]
    print(f"📄 Baixando PDF do inteiro teor: {pdf_url}")

    # 4️⃣ Baixar o PDF (bytes)
    pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
    pdf_response.raise_for_status()
    pdf_bytes = pdf_response.content

    # 5️⃣ Ler o PDF diretamente da memória
    reader = PdfReader(BytesIO(pdf_bytes))
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() or ""

    # 6️⃣ Definir nome do arquivo TXT
    nome_arquivo_txt = f"proposicao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    # 7️⃣ Salvar texto (S3 ou local)
    if bucket_s3:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=bucket_s3,
            Key=nome_arquivo_txt,
            Body=texto.encode("utf-8"),
            ContentType="text/plain"
        )
        print(f"✅ Texto salvo no S3: s3://{bucket_s3}/{nome_arquivo_txt}")
    else:
        with open(f"src/data/{nome_arquivo_txt}", "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"✅ Texto salvo localmente: {nome_arquivo_txt}")

    return texto


if __name__ == "__main__":
    fetch_individual_project(
        "https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2570616"
    )
