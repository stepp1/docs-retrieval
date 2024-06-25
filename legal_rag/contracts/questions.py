from typing import List

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class Question(BaseModel):
    name: str
    answer_template: str
    prompt: str = None
    description: str = None


class Answer(BaseModel):
    "Answer to the question asked"
    text: str
    question_answered: Question = None
    is_answered: bool = False
    page: int = None


class AnswerSet(BaseModel):
    answers: List[Answer]


alcances = Question(
    name="Alcance de Servicios",
    description="Determina cuáles son los servicios que se van a prestar bajo este contrato",
    answer_template="El contrato describe el servicio [Nombre_Servicio]. Este servicio corresponde a [Descripcion]. El servicio se llevará a cabo en [Lugar]",
    prompt="""
        Devuelve la frase anterior completando las partes que están con []. Para esto:

        1) [Nombre_Servicio]: completar con el nombre del servicio.
        2) [Descripcion]: completar con dos frases describiendo el servicio.
        3) [Lugar]: completar con el lugar donde se realizará el servicio.
        NO devuelvas las respuestas a estos pedidos. Solamente devuelve la frase completada.
        """,
)


vigencia = Question(
    name="Vigencia del Contrato",
    description="Determina la duración del contrato",
    answer_template="La Fecha de Acceso es [Fecha_Acceso], mientras que la Fecha de Cumplimiento es [Fecha_Cumplimiento]. La duración es de [Duración].",
    prompt="""
        Devuelve la frase anterior completando las partes que están con []. Para esto:
        
        1) [Fecha_Acceso]: completar con la Fecha de Acceso.
        2) [Fecha_Cumplimiento]: completar con la Fecha de Cumplimiento.
        3) [Duración]: completar con la diferencia entre Fecha_Acceso y Fecha_Cumplimiento, en meses.
        NO devuelvas las respuestas a estos pedidos. Solamente devuelve la frase completada.
        """,
)

terminacion = Question(
    name="Terminación Anticipada",
    description="Determina cuáles los términos de la terminación anticipada del contrato",
    answer_template="La terminación anticipada se debe avisar con [Anticipacion] de anticipación. En caso de que se termine el contrato por esta vía, la Compañía deberá [Obligaciones_Compañía]. Por otra parte, el Contratista deberá [Obligaciones_Contratista].",
    prompt="""
    Devuelve la frase anterior completando las partes que están con []. Para esto:

    1) [Anticipacion]: completar con la cantidad de días de antelación con la que la Compañía para dar aviso escrito al Contratista si desea terminar este Contrato.
    2) [Obligaciones_Compañía]: completar con los pagos que debe realizar la Compañía al Contratista se termina el Contrato o si la Compañía está satisfecha con el Reclamo Escrito que ha sido preparado.
    3) [Obligaciones_Contratista]: : completar con qué debe hacer el Contratista si el contrato se termina de conformidad de la cláusula.
    NO devuelvas las respuestas a estos pedidos. Solamente devuelve la frase completada.
    """,
)

kpis = Question(
    name="Indicadores Clave de Desempeño",
    description="Determina si el contrato posee Indicadores Clave de Desempeño y cuáles son estos.",
    answer_template="El contrato [Existencia] posee Indicadores Clave de Desempeño. [Lista]",
    prompt="""
    Devuelve la frase anterior completando las partes que están con []. Para esto:

    1) [Existencia]: completar con "Sí" o "No" a la pregunta: "¿El contrato posee Indicadores Clave de Desempeño?".
    2) [Lista]: Si en [Existencia] respondiste "Sí", completa con una lista de los Indicadores Clave de Desempeño del contrato.
    NO devuelvas las respuestas a estos pedidos. Solamente devuelve la frase completada.
    """,
)

all_questions = {
    alcances.name: alcances,
    vigencia.name: vigencia,
    terminacion.name: terminacion,
    kpis.name: kpis,
}


def qa_parser():
    parser = PydanticOutputParser(pydantic_object=Answer)
    format_instructions = parser.get_format_instructions()
    return parser, format_instructions
