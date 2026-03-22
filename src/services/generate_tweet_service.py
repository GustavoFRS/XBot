from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

class ThreadFormattedResponse(BaseModel):
    ementa_post: str = Field(min_length=50, max_length=200)
    pontos_post: str = Field(min_length=50, max_length=240)
    justificativa_post: str = Field(min_length=30, max_length=180)


class ProjetoLeiPost(BaseModel):
    numero: str
    autor: str
    partido: str
    uf: str
    link: str

    ementa_post: str
    pontos_post: str
    justificativa_post: str

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
) -> dict:

    client = OpenAI(api_key=api_key)

    system_prompt = """
    Você é um assistente especializado em resumir Projetos de Lei da Câmara dos Deputados.

    Seu objetivo é gerar conteúdo OTIMIZADO para threads no X (Twitter).

    Regras:

    1. Responda apenas em JSON válido:
    {
      "ementa_post": "...",
      "pontos_post": "...",
      "justificativa_post": "..."
    }

    2. ementa_post:
    - até 200 caracteres
    - resumo claro da proposta

    3. pontos_post:
    - até 240 caracteres
    - 1 a 3 bullets no formato:
      "- texto"

    4. justificativa_post:
    - até 180 caracteres
    - frase única

    5. NÃO inclua títulos
    6. NÃO ultrapasse limites
    7. Seja direto e objetivo
    """

    user_prompt = f"""
    Ementa:
    {ementa}

    Texto completo:
    {text}
    """

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        text_format=ThreadFormattedResponse,
        temperature=0.4,
    )

    parsed = response.output_parsed

    # fallback defensivo (ESSENCIAL)
    def truncate(text, limit):
        return text if len(text) <= limit else text[:limit - 3] + "..."

    result = ProjetoLeiPost(
        numero=numero_pec,
        autor=autor,
        partido=partido,
        uf=uf,
        link=link,
        ementa_post=truncate(parsed.ementa_post, 200),
        pontos_post=truncate(parsed.pontos_post, 240),
        justificativa_post=truncate(parsed.justificativa_post, 180),
    )

    return result.model_dump()