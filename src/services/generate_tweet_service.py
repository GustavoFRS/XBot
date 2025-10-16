import os
import openai
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from typing import List

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class SummaryResponse(BaseModel):
    pontos_chave: List[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="Lista de 1 a 4 pontos principais extraídos do texto."
    )
    justificativa: str = Field(
        ...,
        min_length=10,
        max_length=180,
        description="Resumo curto da justificativa do projeto (até 180 caracteres)."
    )

def forbid_additional_properties(schema: dict) -> dict:
    """
    Varre o JSON Schema e força additionalProperties: false em todos os objetos.
    """
    if not isinstance(schema, dict):
        return schema

    # Se é um objeto, garanta o additionalProperties
    if schema.get("type") == "object":
        schema.setdefault("additionalProperties", False)

    # Varre recursivamente propriedades aninhadas
    for _, value in list(schema.items()):
        if isinstance(value, dict):
            forbid_additional_properties(value)
        elif isinstance(value, list):
            for item in value:
                forbid_additional_properties(item)

    return schema

def generate_tweet(
    text: str,
    numero_pec: str,
    autor: str,
    partido: str,
    uf: str,
    ementa: str,
    link: str
) -> str:
    """
    Gera o conteúdo completo de um tweet, a partir do texto da proposição.
    Apenas os pontos-chave e a justificativa são gerados por IA.
    """

    system_prompt = """
    Você é um assistente especializado em resumir Projetos de Lei e PECs da Câmara dos Deputados do Brasil.

    Seu objetivo é extrair informações de forma sintética, neutra e fiel ao texto fornecido.
    Siga estas regras com rigor:

    1. Gere a resposta ESTRITAMENTE em formato JSON válido.
    2. O JSON deve conter exatamente:
    {
        "pontos_chave": ["string", "string"],
        "justificativa": "string"
    }
    3. `pontos_chave` deve ser uma lista de 1 a 4 frases curtas (máximo 100 caracteres cada).
    4. `justificativa` deve ser uma frase única (máximo 180 caracteres) explicando a motivação do projeto.
    5. Não use comentários, explicações ou texto fora do JSON.
    6. Responda em português, de forma clara e objetiva.
    """

    user_prompt = f"""
    Texto do projeto de lei a ser resumido:

    {text}

    Gere a saída seguindo estritamente as instruções acima.
    """


    schema = forbid_additional_properties(SummaryResponse.model_json_schema())

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_prompt}, 
            {"role": "system", "content": system_prompt}
            ],
        temperature=0.4,
        response_format={
            "type": "json_object"
        }
    )

    content = response.choices[0].message.content

    try:
        data = SummaryResponse.model_validate_json(content)
    except ValidationError as e:
        print("❌ Resposta inválida, ajustando com fallback:", e)
        fix_prompt = f"""
        Corrija o JSON abaixo para seguir estritamente o schema:
        - 1 a 4 pontos em 'pontos_chave'
        - 'justificativa' com até 180 caracteres
        Retorne apenas o JSON corrigido.

        JSON original:
        {content}
        """
        fix_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        data = SummaryResponse.model_validate_json(fix_response.choices[0].message.content)

    pontos = "\n".join([f"    - {p}" for p in data.pontos_chave])
    tweet = (
        f"PL/PEC {numero_pec}\n"
        f"Autor: {autor} ({partido}-{uf})\n\n"
        f"{ementa}\n"
        f"Pontos-chave:\n{pontos}\n"
        f"Justificativa: {data.justificativa}\n"
        f"Link: {link}"
    )

    return tweet

if __name__ == "__main__":
    with open("src/data/proposicao_20251014_112450.txt", "r", encoding="utf-8") as f:
        text = f.read()
    print(generate_tweet(
        text=text,
        numero_pec="PL 5095/2025",
        autor="Kim Kataguiri",
        partido="União",
        uf="SP",
        ementa="Confere imunidade Penal e Civil para qualquer pessoa que faça crítica, mesmo que ofensiva, a membro dos poderes Executivo, Legislativo e Judiciário.",
        link="http://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2570616"
    ))