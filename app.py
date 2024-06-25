import json
import logging
import os
import sys
import time
from functools import partial

import streamlit as st

cwd = os.getcwd()
# update path
if cwd not in sys.path:
    sys.path.append(cwd)

from legal_rag.contracts.parsing import Section
from legal_rag.contracts.prompts import Context, build_context, build_prompt
from legal_rag.contracts.questions import Question, all_questions, qa_parser
from legal_rag.contracts.utils import select_index_section
from legal_rag.loaders import parse_pdf
from legal_rag.models.oai import native_oai_chain
from legal_rag.utils import display_document

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("demo_app:main")

USE_THREADS = False  # not working
OAI_MODEL_NAME = "gpt-4"  # "gpt-4-1106-preview"
CRITERIA = "lexico"  # "semantica"
LAST_CALL_OAI = ...


def st_build_context(pages, doc_index, selected_questions) -> Context:
    """
    Build the context for the selected questions.
    Might use threads to not wait for the context to be built.
    """

    # Using criteria=semantica takes at least 2 minutes to run
    # @st.cache_data
    def st_select_index_section(raw_sections, q_name, criteria="semantica"):
        if q_name == "Indicadores Clave de Desempeño":
            raw_sections = [
                s for s in raw_sections if s["name"] in doc_index.annex_names
            ]
        selected_section = select_index_section(raw_sections, q_name, criteria=criteria)
        return selected_section

    # select section using raw sections, this is used to cache the results
    logging.info("Selecting section")
    raw_sections = [json.loads(s.model_dump_json()) for s in doc_index.sections]
    selected_section = st_select_index_section(raw_sections, selected_questions.name)
    selected_section = Section(**selected_section)

    context_fn = partial(build_context, selected_section=selected_section, pages=pages)
    logging.info("Returning Context and thread")
    return context_fn()


def select_question_set() -> Question:
    """
    Display a select widget with the different question sets.
    """
    st.markdown("### Questions")
    qset_name = st.selectbox(
        "Select a set of questions:",
        ("Select",) + tuple([q.name for q in all_questions.values()]),
    )

    if qset_name != "Seleccione":
        qset = all_questions[qset_name]
        logger.info(f"Selected question set: {qset.name}")
        return qset

    logger.warning("No question set was selected.")
    return None


def run_pipeline(pages, doc_index, qset, uploaded_file=None):
    logging.info("Displaying questions")
    st.write(f"### You've selected the following question set: {qset.name}")
    st.write(f"Questions are: **{qset.description or qset.name}**.")

    if (
        qset.name == "Indicadores Clave de Desempeño"
        and not doc_index.contains_kpi_annex
    ):
        st.write(f"**No KPI appendix was found.**")
        return None, None

    ctx = st_build_context(pages, doc_index, qset)
    parser, format_instructions = qa_parser()
    extraction_prompt = build_prompt(
        selected_questions=qset, format_instructions=format_instructions
    )
    if ctx is None:
        raise ValueError("Context is None")

    # logger.info(extraction_prompt.format(context=ctx.str_context)[:1000])
    logger.info(f"Context: {ctx.section_name}, starts at page {ctx.page}")

    # sleep 3 seconds to give time to the user to read the text
    time.sleep(3)
    # write a quote in markdown with the selected section name
    st.write(f"### Searching answer in {ctx.section_name}")

    # print loading circle animation while the questions are being answered
    with st.spinner("Answering questions... This might take a while..."):
        logger.info(
            f"Running pipeline with: qset={qset.name}, pages={len(pages)}, doc_index={len(doc_index.sections)}"
        )
        response, kind_str = native_oai_chain(
            extraction_prompt, ctx, model_name=OAI_MODEL_NAME
        )
        logger.info(f"Response: {response}, type: {type(response)}")

    if kind_str == "answerset":
        for k, answer in enumerate(response.answers):
            st.write(f"- **{answer.question_answered.name}**:")
            st.write(f"{answer.text}")

    elif kind_str == "json":
        for k, question_str in enumerate(qset.questions):
            r = response[k]
            st.write(f"**{question_str}**:")
            st.write(f"{r}")

    else:
        logger.warning(f"Response is not a json nor an AnswerSet: {type(response)}")
        st.write(f"{response}")
    # with col2:

    if display_document is not None:
        display_document(
            uploaded_file=uploaded_file,
            specific_page=ctx.context[0].metadata["page"] + 1,
        )

    return ctx, response


def main():
    # Set the title and description of the app
    st.title("Document Augmented Retrieval for Legal Documents")
    st.write("Upload a legal document and ask questions about it.")
    pages, doc_index, qset = None, None, None

    # Create a file upload widget
    uploaded_file = st.file_uploader(
        "Select a document...", type=["pdf", "docx", "txt"]
    )

    if uploaded_file is None:
        st.info("Suba un contrato.")

    elif uploaded_file is not None:
        # HERE: [threading] we can use threads to not wait for the file to be parsed
        with st.spinner("Extracting text from the document..."):
            results = parse_pdf(uploaded_file)

        pages, doc_index = results[0], results[1]
        st.write("**Retrieving info on:**")
        st.write(f"{pages[0].metadata['file_name']}")
        qset = select_question_set()

        if qset is None:
            pass
        elif pages is not None and doc_index is not None:
            logger.info(
                f"Running pipeline with: qset={qset.name}, pages={len(pages)}, doc_index={len(doc_index.sections)}"
            )

            ctx, response = run_pipeline(
                pages=pages, doc_index=doc_index, qset=qset, uploaded_file=uploaded_file
            )
    else:
        st.error("Loading error.")


if __name__ == "__main__":
    main()
