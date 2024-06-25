import logging
from functools import partial
import os

import instructor
import openai
import streamlit as st
from legal_rag.contracts.questions import AnswerSet
from legal_rag.utils import check_streamlit

DEFAULT_MODEL_NAME = "gpt-4-1106-preview"

def load_env_var(var_name):
    return os.getenv(var_name)

def native_oai_chain(
    extraction_prompt, ctx, model_name=DEFAULT_MODEL_NAME
) -> AnswerSet:
    openai.api_key = load_env_var("OPENAI_API_KEY")

    logging.info("Patching OpenAI API w/ instructor")
    client = instructor.patch(openai.OpenAI(api_key=openai.api_key))
    completion_create_fn = partial(
        client.chat.completions.create,
        model=model_name,
    )

    @st.cache_resource
    def st_oai_call(str_ctx):
        response = completion_create_fn(
            response_model=AnswerSet,
            messages=[
                {
                    "role": "system",
                    "content": extraction_prompt.format(context=str_ctx),
                },
                {"role": "user", "content": "Answers: ..."},
            ],
            max_tokens=1000,
            temperature=0.1,
        )
        return response

    def oai_call(str_ctx):
        response = completion_create_fn(
            response_model=AnswerSet,
            messages=[
                {
                    "role": "system",
                    "content": extraction_prompt.format(context=str_ctx),
                },
                {"role": "user", "content": "Answers: ..."},
            ],
            max_tokens=4000,
            temperature=0.1,
        )
        return response

    response = st_oai_call(ctx.str_context) if check_streamlit() else oai_call
    # check if the response is an AnswerSet
    is_answerset = hasattr(response, "answers")
    # check if the response is a str json
    is_json = isinstance(response, str) and response.startswith("{")
    return response, "answerset" if is_answerset else "json" if is_json else "unknown"
