import requests

def fetch_projects_csv(
    tipos="PEC,PL",
    pagina=1,
    ordem="data",
    termo_busca="",
    caminho_arquivo="proposicoes_all.csv"
):
    """
    Envia requisição à API da Câmara e baixa o CSV de proposições.
    """
    url = "https://www.camara.leg.br/busca-download/api/v1/arquivo/proposicoes"
    payload = {
        "data": {
            "order": ordem,
            "pagina": pagina,
            "q": termo_busca,
            "tiposDeProposicao": tipos
        },
        "formato": "csv"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "text/csv;=;charset=utf-8"
    }

    try:
        print(f"📡 Baixando CSV da página {pagina} ({tipos})...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        with open(caminho_arquivo, "wb") as f:
            f.write(response.content)

        print(f"✅ Arquivo salvo em: {caminho_arquivo}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao baixar CSV: {e}")