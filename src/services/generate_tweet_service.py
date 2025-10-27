import openai
from pydantic import BaseModel, Field, ValidationError
from typing import List
from pydantic import field_validator

class ProjetoLeiJSON(BaseModel):
    numero: str
    autor: str
    partido: str
    uf: str
    ementa_original: str
    ementa_resumida: str
    pontos_chave: List[str]
    justificativa: str
    link: str


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

    @field_validator('pontos_chave', mode="after")
    @classmethod
    def validar_total_chars(cls, v):
        """
        Valida se a soma total de caracteres dos pontos-chave não excede 285.
        """
        total_chars = sum(len(item) for item in v)
        if total_chars > 285:
            raise ValueError(f"Total de caracteres excedido: {total_chars} > 285")

        return v

def resumir_ementa(api_key: str, ementa: str, max_chars: int = 300) -> str:
    """Se a ementa for longa, resume-a para até 300 caracteres usando IA."""
    if len(ementa) <= max_chars:
        return ementa

    openai.api_key = api_key
    prompt = f"""
    Resuma o texto abaixo para no máximo {max_chars} caracteres, mantendo o sentido e a clareza.
    Texto: {ementa}
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    resumo = response.choices[0].message.content.strip()
    return resumo


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
    openai.api_key = api_key

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

    
    # Monta o JSON final
    projeto_json = ProjetoLeiJSON(
        numero=numero_pec,
        autor=autor,
        partido=partido,
        uf=uf,
        ementa_original=ementa,
        ementa_resumida=ementa_resumida,
        pontos_chave=data.pontos_chave,
        justificativa=data.justificativa,
        link=link
    )

    return projeto_json.model_dump()