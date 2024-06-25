import logging
from typing import Dict, Sequence, Union

import numpy as np
import textdistance
from sentence_transformers import SentenceTransformer, util

diccionario_keywords = {
    "Alcance de Servicios": [
        "ALCANCE DE LOS SERVICIOS",
        "DESCRIPCIÓN DE LOS SERVICIOS",
        "SCOPE OF SERVICES",
        "alcance tecnico",
        "SCHEDULE",
    ],
    "Vigencia del Contrato": [
        "fecha de acceso",
        "fecha de cumplimiento",
        "Especificaciones del contrato",
        "CONTRACT SPECIFICS",
    ],
    "Terminación Anticipada": [
        "NO CONFORMIDADES", 
        "Terminación Contrato", 
        "ENDING THIS CONTRACT",
        ],
    "Indicadores Clave de Desempeño": [
        "INDICADORES CLAVE DE DESEMPEÑO",
        "INDICADORES CLAVES DE DESEMPEÑO",
        "Key Performance Indicators",
        "Anexo",
        "SCHEDULE",
    ],
}


def get_similarity(
    criteria: str,
    a: Union[Sequence[str], str],
    b: Union[Sequence[str], str],
    model=None,
) -> Union[float, Sequence[float]]:
    criterion = (
        util.pytorch_cos_sim if criteria == "semantica" else textdistance.Cosine()
    )

    if criteria == "semantica":
        model = (
            SentenceTransformer("hiiamsid/sentence_similarity_spanish_es")
            if model is None
            else model
        )
        a = model.encode(a, convert_to_tensor=True)
        b = model.encode(b, convert_to_tensor=True)

    return criterion(a, b)


def select_index_section(
    raw_sections: Dict[str, str], q_set_name: str, criteria="lexico"
) -> str:
    """
    Given the question set and the document index, select the section that matches the question set.

    This runs a lexicographic similarity search between the question set name and the document index.
    """
    most_likely_section = None
    query_names = [pos_name.lower() for pos_name in diccionario_keywords[q_set_name]]
    name_raw_sections = [sec["name"].lower() for sec in raw_sections]

    # Dado que tenemos el nombre de la query, obtenemos los posibles nombres
    # de secciones para poder realizar una busqueda por similaridad
    # A continuacion buscamos usando los posibles nombres de seccion, la seccion del documento que mejor matchee

    if criteria == "semantica":
        result = get_similarity("semantica", query_names, name_raw_sections).mean(dim=0)
        selected_idx = result.argmax().item()

    elif criteria == "lexico":
        result = np.mean(
            [
                [get_similarity("lexico", q, v) for q in query_names]
                for v in name_raw_sections
            ],
            axis=1,
        )
        selected_idx = result.argmax()
    else:
        raise ValueError(f"Criteria {criteria} not supported")

    to_log = [(result, s_name) for s_name in name_raw_sections]
    logging.info(f"Similarity: {to_log}")
    most_likely_section = raw_sections[selected_idx]

    logging.info(f"Most likely section: {most_likely_section}")
    return most_likely_section
