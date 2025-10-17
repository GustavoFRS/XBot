import requests
from io import BytesIO
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup

def fetch_individual_project(prop: dict):
    """
    Recebe uma proposição (dict) contendo a chave 'Link'.
    Retorna um dicionário com o HTML da página e o texto do inteiro teor (se existir).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    nome = prop.get("Proposições", "desconhecida")
    url = prop.get("Link")

    if not url:
        print(f"⚠️ Proposição {nome} sem link.")
        return {"html": None, "texto": None}

    # 🔹 1. Acessar página HTML
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    html_content = response.text

    # 🔹 2. Tentar encontrar o link do inteiro teor
    soup = BeautifulSoup(html_content, "html.parser")
    link_inteiro_teor = soup.find("a", class_="linkDownloadTeor")

    if not link_inteiro_teor or not link_inteiro_teor.get("href"):
        print(f"⚠️ Nenhum inteiro teor encontrado para {nome}.")
        return {"html": html_content, "texto": None}

    pdf_url = link_inteiro_teor["href"]
    print(f"📄 Baixando PDF do inteiro teor de {nome}: {pdf_url}")

    # 🔹 3. Baixar e extrair texto do PDF
    pdf_response = requests.get(pdf_url, headers=headers, timeout=30)
    pdf_response.raise_for_status()
    reader = PdfReader(BytesIO(pdf_response.content))
    texto = "".join(page.extract_text() or "" for page in reader.pages)

    return {"html": html_content, "texto": texto}
