"""Read PDF files."""

import abc
import io
import logging
import os
import tempfile
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import requests
import streamlit as st
from demo.contracts.parsing import ContractIndex, index_parser
from langchain_core.documents import Document
from streamlit.runtime.uploaded_file_manager import UploadedFile


class BasePDFLoader(abc.ABC):
    def __init__(self, file_or_path: Union[str, UploadedFile], name: str = None):
        self.file_or_path = file_or_path
        self.web_path = None

        if isinstance(self.file_or_path, str):
            file_path, self.web_path = self.get_as_file_path(
                self.file_or_path, headers=None
            )
            # read file as bytes
            with open(file_path, "rb") as f:
                bytes_data = io.BytesIO(f.read())

        else:
            bytes_data = self.file_or_path.getvalue()

        self.name = (
            name if name is not None else self.web_path or self.file_or_path.name
        )
        self.bytes_data = bytes_data

    def get_as_file_path(self, file_path, headers=None):
        if "~" in file_path:
            file_path = os.path.expanduser(file_path)

        # If the file is a web path or S3, download it to a temporary file, and use that
        if not os.path.isfile(file_path) and self._is_valid_url(file_path):
            temp_dir = tempfile.TemporaryDirectory()
            _, suffix = os.path.splitext(file_path)
            temp_pdf = os.path.join(temp_dir.name, f"tmp{suffix}")
            web_path = file_path
            if not self._is_s3_url(file_path):
                r = requests.get(file_path, headers=headers)
                if r.status_code != 200:
                    raise ValueError(
                        "Check the url of your file; returned status code %s"
                        % r.status_code
                    )

                with open(temp_pdf, mode="wb") as f:
                    f.write(r.content)
                file_path = str(temp_pdf)
        elif not os.path.isfile(file_path):
            raise ValueError("File path %s is not a valid file or url" % file_path)
        else:
            web_path = None

        return file_path, web_path

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if the url is valid."""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    @staticmethod
    def _is_s3_url(url: str) -> bool:
        """check if the url is S3"""
        try:
            result = urlparse(url)
            if result.scheme == "s3" and result.netloc:
                return True
            return False
        except ValueError:
            return False


class OnlinePDFLoader(BasePDFLoader):
    """Load online `PDF`."""

    def load(self) -> List[Document]:
        """
        Load documents.

        Flow:
        0. Check if url isif valid
        1. Load file from web path as bytes
        2. Use BytesIO to read bytes into PDFMiner
        """
        raise NotImplementedError(
            "This has not been implemented but will be useful when actually deployed."
        )


class PDFMinerReader(BasePDFLoader):
    """PDF parser based on pdfminer.six."""

    def load_data(self, extra_info: Optional[Dict] = None) -> List[Document]:
        """Parse file."""
        try:
            import io

            from pdfminer.converter import TextConverter
            from pdfminer.layout import LAParams
            from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
            from pdfminer.pdfpage import PDFPage

            def _extract_text_from_page(page):
                resource_manager = PDFResourceManager()
                output_string = io.StringIO()
                codec = "utf-8"
                laparams = LAParams()
                device = TextConverter(
                    resource_manager, output_string, codec=codec, laparams=laparams
                )
                interpreter = PDFPageInterpreter(resource_manager, device)
                interpreter.process_page(page)
                text = output_string.getvalue()
                device.close()
                output_string.close()
                return text

        except ImportError:
            raise ImportError(
                "pdfminer.six is required to read PDF files: `pip install pypdf`"
            )

        # if isinstance(self.bytes_data, io.BytesIO):
        reader = PDFPage.get_pages(io.BytesIO(self.bytes_data))
        docs = []
        for i, page in enumerate(reader):
            page_text = _extract_text_from_page(page)
            metadata = {"page": i, "file_name": self.name}
            if extra_info is not None:
                metadata.update(extra_info)

            docs.append(Document(page_content=page_text, metadata=metadata))
        return docs


# @st.cache_data
def parse_pdf(file: UploadedFile, results=None) -> List[Union[Document, ContractIndex]]:
    """
    Parse a document and return the pages and the index.

    We do it a bit complicated because we do not want to save
    the PDF anywhere, even as a tempfile. Therefore, we read
    the file as bytes, and then we parse it.

    This is basically a wrapper around the PDFMinerParser,
    just as langchain's PDFMinerLoader.
    """
    logging.info(f"Received file: {file.name} of type {file.type}")

    s_time = time.time()
    # load pdf
    reader = PDFMinerReader(file)
    pages = reader.load_data()
    print(pages[0])
    contract_index = index_parser(pages)
    n_paginas = len(pages)

    logging.info(f"Loaded {n_paginas} pages in {time.time() - s_time} seconds")
    logging.info(
        f"ContractIndex has: {len(contract_index.sections)} sections, {len(contract_index.annex_names)} annex names, {contract_index.contains_kpi_annex} -> wrt. a KPI Annex"
    )
    
    logging.info(f"Found sections: {contract_index.sections}")
    logging.info(f"Found annex names: {contract_index.annex_names}")
    logging.info(f"Contains KPI Annex: {contract_index.contains_kpi_annex}")

    if results is not None:
        results[0] = pages
        results[1] = contract_index
    else:
        results = [pages, contract_index]

    return results
