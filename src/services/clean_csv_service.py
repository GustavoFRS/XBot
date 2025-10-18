import pandas as pd
import numpy as np
from datetime import datetime
from slugify import slugify

def clean_csv(caminho_arquivo: str):
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
        
        # 🔎 Filtra proposições apresentadas hoje
        df_hoje = df[df["Apresentação"] == hoje]

        # Slugify
        df_hoje['Proposições_slugified'] = df_hoje['Proposições'].apply(slugify)

        # Remove NaN
        df_hoje = df_hoje.replace({np.nan: None})

        print(f"📊 {len(df_hoje)} proposições encontradas com data {hoje}.")
        return df_hoje

    except Exception as e:
        print(f"❌ Erro ao limpar CSV: {e}")
        raise e
