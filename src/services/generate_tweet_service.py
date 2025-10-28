from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from typing import List
from pydantic import field_validator

class ProjetoLeiJSON(BaseModel):
    numero: str
    autor: str
    partido: str
    uf: str = Field(..., min_length=2, max_length=4)
    ementa_original: str
    ementa_resumida: str = Field(..., min_length=1, max_length=300)
    pontos_chave: List[str]
    justificativa: str
    link: str

class PontoChave(BaseModel):
    ponto: str = Field(..., min_length=1, max_length=95)

class SummaryResponse(BaseModel):
    pontos_chave: List[PontoChave] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Lista de 1 a 3 pontos principais extraídos do texto."
    )
    justificativa: str = Field(
        ...,
        min_length=10,
        max_length=180,
        description="Resumo curto da justificativa do projeto (até 180 caracteres)."
    )


def resumir_ementa(api_key: str, ementa: str, max_chars: int = 300) -> str:
    """Se a ementa for longa, resume-a para até 300 caracteres usando IA."""    
    if len(ementa) <= max_chars:
        return ementa

    class ResumoEmenta(BaseModel):
        resumo: str = Field(..., min_length=1, max_length=max_chars)
    
    client = OpenAI(api_key=api_key)

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system", 
                "content": f"Resuma o texto abaixo para no máximo {max_chars} caracteres, mantendo o sentido e a clareza."
            },
            {
                "role": "user", 
                "content": ementa
            }
        ],
        text_format=ResumoEmenta,
        temperature=0.4,
    )

    return response.output_parsed.resumo


def gerar_resumo(
    api_key: str,
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
    # Define chave
    client = OpenAI(api_key=api_key)

    ementa_resumida = resumir_ementa(api_key, ementa, max_chars=300)

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
    3. `pontos_chave` deve ser uma lista de 1 a 4 frases curtas (somadas devem ter um máximo de 285 caracteres).
    4. `justificativa` deve ser uma frase única (máximo 180 caracteres) explicando a motivação do projeto.
    5. Não use comentários, explicações ou texto fora do JSON.
    6. Responda em português, de forma clara e objetiva.
    """

    user_prompt = f"""
    Texto do projeto de lei a ser resumido:

    {text}

    Gere a saída seguindo estritamente as instruções acima.
    """

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "user", "content": user_prompt}, 
            {"role": "system", "content": system_prompt}
            ],
        text_format=SummaryResponse,
        temperature=0.4,
    )

    event = response.output_parsed

    # Monta o JSON final
    projeto_json = ProjetoLeiJSON(
        numero=numero_pec,
        autor=autor,
        partido=partido,
        uf=uf,
        ementa_original=ementa,
        ementa_resumida=ementa_resumida,
        pontos_chave=[p.ponto for p in event.pontos_chave],
        justificativa=event.justificativa,
        link=link
    )

    return projeto_json.model_dump()