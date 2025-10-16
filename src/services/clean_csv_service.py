import pandas as pd
from datetime import datetime

def clean_csv(caminho_arquivo="src/data/proposicoes.csv"):
    """
    Limpa o CSV da Câmara e retorna as proposições apresentadas hoje.
    """
    try:
        # 📥 Lê o CSV, pulando as 3 primeiras linhas (metadados)
        df = pd.read_csv(caminho_arquivo, skiprows=3, sep=";", encoding="utf-8")

        # 🧹 Remove linhas completamente vazias
        df = df.dropna(how="all")

        # 🗓️ Data de hoje no formato dd/mm/yyyy
        hoje = datetime.today().strftime("%d/%m/%Y")

        # TODO:
        # 📊 Remove colunas desnecessárias
        # slugify df["Proposições"] (mudar nome da coluna -> id)
        
        # 🔎 Filtra proposições apresentadas hoje
        df_hoje = df[df["Apresentação"] == hoje]
        df_hoje.to_csv("src/data/proposicoes_hoje.csv", index=False)

        print(f"📊 {len(df_hoje)} proposições encontradas com data {hoje}.")
        return df_hoje

    except Exception as e:
        print(f"❌ Erro ao limpar CSV: {e}")
        return pd.DataFrame()
