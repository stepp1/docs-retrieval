from dataclasses import dataclass
from typing import List

from langchain.prompts import PromptTemplate
from llama_index import Document

TRUNCATE = 8192


@dataclass
class Context:
    context: List[Document]
    str_context: str
    section_name: str
    page: int


system_prompt = """
Eres un asistente de leyes especializado en minería. Tienes acceso a ciertas parte de contratos de servicios para responder preguntas sobre estos.
Mantente estrictamente al formato y no añadas información o caracteres extra. 
Para responder tendras accesso a una seccion contrato a la vez. Responde las preguntas, actualiza el campo is_answered e indica a que pregunta corresponde en el campo question_answered.

{format_instructions}

Se te pide responder de  siguientes preguntas:
{questions}

"Sección del Contrato: {context}\n"
"""


def build_prompt(selected_questions, format_instructions):
    extraction_prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["context"],
        partial_variables={
            "format_instructions": format_instructions,
            "questions": selected_questions.json(),
        },
    )

    return extraction_prompt


# Funcion para truncar el contexto a menos de 10000 tokens
# Esencialmente esto deberia funcionar
# Algo que podria ser mejor es hacer similarity search dentro de la seccion para enviar solo los chunks con mayor probabilidad de contener lo solicitado
def truncate_tokens(tokens, max_len=7192):
    tokens = tokens.rstrip().lstrip().replace("\n", " ")

    final_max_len = max_len - len(system_prompt)

    if len(tokens) <= final_max_len:
        return tokens
    else:
        return tokens[:final_max_len]


def build_context(
    selected_section,
    pages,
    truncate_len=None,
    results=None,
):
    context = pages[selected_section.start_page : selected_section.end_page]
    str_context = "\n".join([page.page_content for page in context])
    str_context = truncate_tokens(str_context, max_len=truncate_len or TRUNCATE)

    try:
        ctx = Context(
            context=context,
            str_context=str_context,
            section_name=selected_section.name,
            page=selected_section.start_page,
        )

    except Exception as e:
        print(e)
        print(context)
        print(len(str_context))
        print(selected_section.name)
        return context, str_context, selected_section.name

    if results is not None and len(results) == 1:
        results[0] = ctx

    return ctx
