import base64
import io

import streamlit as st


def check_streamlit():
    """
    Function to check whether python code is run within streamlit

    Returns
    -------
    use_streamlit : boolean
        True if code is run within streamlit, else False
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if not get_script_run_ctx():
            use_streamlit = False
        else:
            use_streamlit = True
    except ModuleNotFoundError:
        use_streamlit = False
    return use_streamlit


def display_document(uploaded_file: io.BytesIO, specific_page: int = None):
    """
    Display the contents of a file on Streamlit.
    """
    # Display the document using an iframe
    if uploaded_file.type == "application/pdf":
        # For PDF files
        pdf_bytes = uploaded_file.read()
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{base64_pdf}#page={specific_page}" width="900" height="800"></iframe>',
            unsafe_allow_html=True,
        )
    elif (
        uploaded_file.type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        # For Word documents (docx)
        st.warning(
            "Word documents are not supported for direct display. You can download the file instead."
        )
        st.download_button("Download Document", uploaded_file)
    elif uploaded_file.type == "text/plain":
        # For plain text documents (txt)
        txt_content = uploaded_file.read().decode("utf-8")
        st.text(txt_content)
    else:
        st.warning(
            "Unsupported file format. Please upload a PDF, Word document (docx), or plain text (txt)."
        )
