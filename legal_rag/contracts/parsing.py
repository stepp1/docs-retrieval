import logging
from typing import List

from demo.contracts.utils import diccionario_keywords
from pydantic import BaseModel
from unidecode import unidecode


class Section(BaseModel):
    name: str
    start_page: int
    end_page: int


class ContractIndex(BaseModel):
    page: int
    sections: List[Section]
    annex_names: List[str]
    contains_kpi_annex: bool


nombres_especificaciones = ["especificaciones del contrato", "contract specifics"]


def clean_lines(lines):
    # remove leading digits
    lines = [line.lstrip("0123456789") for line in lines]
    # lstrip whitespaces and \n
    lines = [line.lstrip().rstrip() for line in lines]
    lines = [line.strip(".") for line in lines]
    lines = [line.strip("\n") for line in lines]
    # rstrip whitespaces
    lines = [line.rstrip() for line in lines]
    # if a line is empty, remove it
    lines = [line for line in lines if line != ""]
    # if a line is just a number, remove it
    lines = [line for line in lines if not line.isdigit()]
    # if a line startswith indice or index, remove it
    lines = [line for line in lines if not unidecode(line).lower().startswith("indice")]
    lines = [
        line for line in lines if not unidecode(line).lower().startswith("contenido")
    ]
    return lines


def index_parser(contrato) -> dict:
    n_paginas = len(contrato)

    def add_end_token(lines):
        for i, line in enumerate(lines):
            if "..." in line:
                # go to last dot
                last_dot = line.rfind(".")
                # replace this dot by END
                line = line[:last_dot] + "[END]" + line[last_dot + 1 :]
                # replace all dots by ""
                line = line.replace(".", "")
                lines[i] = line
            else:
                lines[i] = ""
        return [line for line in lines if line != ""]

    pages_with_index = []
    for i in range(0, n_paginas // 4):
        if "..." in contrato[i].page_content:
            logging.info(f"Page {i} has index")
            pages_with_index.append(contrato[i])

    if len(pages_with_index) == 0:
        raise ValueError("No se pudo encontrar el indice")
    else:
        index_start_page = pages_with_index[0].metadata["page"]
        index_last_page = pages_with_index[-1].metadata["page"]

    for i, page_as_doc in enumerate(pages_with_index):
        page_str = page_as_doc.page_content

        lines = page_str.split("\n\n")
        lines = clean_lines(lines)
        # in each line if line contains a set of dots, replace the dots by -
        lines = add_end_token(lines)
        pages_with_index[i] = lines

    dict_index = {}
    page_delta = 0
    for lines in pages_with_index:
        for line in lines:
            try:
                # separate by END
                index_name, page = "".join(line).split("[END]")
            except ValueError:
                logging.warning(f"{line}")
                raise ValueError("No se pudo separar el indice de la pagina")
            index_name = index_name.rstrip().lstrip()

            page = page.replace("[END]", "")
            page = page.replace(" ", "")
            page = page.rstrip().lstrip()

            # check if starts with a number
            while index_name.startswith(tuple("0123456789")):
                index_name = index_name[1:]

            index_name = index_name.rstrip().lstrip()

            # check if index_name is not empty
            if index_name != "" and page.isdigit():
                # esto es ya que puede ser que la especificaciones,
                # que deberia la primera seccion, no este bien numerado
                if index_name.lower() in nombres_especificaciones and page == "1":
                    page_delta = index_last_page + 1

                dict_index[index_name] = int(page) + page_delta

    sections = []
    for key, value in dict_index.items():
        sections.append(
            Section(
                name=key,
                start_page=value - 1,
                end_page=get_page_end(value, dict_index, n_paginas),
            )
        )

    # Check if any section.name is within annex_kws
    annex_kws = {"anexo", "schedule", "annex"}
    annex_names = []
    for section in sections:
        for kw in annex_kws:
            if kw in section.name.lower():
                annex_names.append(section.name)
                break

    if len(annex_names) > 0:
        annex_names = list(annex_names)

    kpis_kws = {
        kw.lower() for kw in diccionario_keywords["Indicadores Clave de Desempeño"]
    }
    kpis_kws = kpis_kws - set(annex_kws)  # this keeps only names of annexes

    # for all annex_names, if any of them contains any kpis_kws as substring
    contains_kpi_annex = False
    for annex_name in annex_names:
        print(annex_name, kpis_kws)
        if any(kw in annex_name.lower() for kw in kpis_kws):
            contains_kpi_annex = True
            break

    return ContractIndex(
        page=index_start_page,
        sections=sections,
        annex_names=list(annex_names) if len(annex_names) > 0 else [],
        contains_kpi_annex=contains_kpi_annex,
    )


# Va agregar 4 paginas extras las necesite o no, a priori se considera que siempre la page_start es menor o igual a la pagina de inicio correcta
def get_page_end(page_start, doc_index, cantidad_paginas):
    for page in doc_index.values():
        if page > page_start:
            if page + 4 >= cantidad_paginas:
                return cantidad_paginas - 1
            return page + 4
    # Si no hay seccion que termine despues de la page_start, entonces es la ultima seccion y su end_page es la ultima pagina
    return cantidad_paginas - 1
