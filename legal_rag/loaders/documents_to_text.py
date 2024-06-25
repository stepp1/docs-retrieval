import re
import string

import textdistance
from unstructured.documents.elements import NarrativeText
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text_type import sentence_count

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    pass

try:
    from unstructured.partition.docx import partition_docx

    docx_available = True
except ImportError:
    docx_available = False

try:
    from unstructured.partition.xlsx import partition_xlsx

    xlsx_available = True
except ImportError:
    xlsx_available = False


def get_string_from_list(lista):
    resultado = ""
    for word in lista:
        resultado += " " + word

    return resultado


class TextExtractor:
    # Quizá seria más convienente guardar el output del partitioner para los documentos
    def __init__(self, lan, tokenizer=None, stopwords=None):
        self.lan = lan
        self.tokenizer = tokenizer
        self.stopwords = stopwords

    def get_text_from_pdf(self, pdf_file_route):
        usando_pdf_partition = partition_pdf(pdf_file_route)
        text_in_pdf_partition = ""
        for el in usando_pdf_partition:
            text_in_pdf_partition = text_in_pdf_partition + " " + str(el)

        return text_in_pdf_partition

    def get_text_from_docx(self, docx_file_route):
        if not docx_available:
            raise ImportError("docx is not available")

        usando_docx_partition = partition_docx(filename=docx_file_route)
        text_in_docx_partition = ""
        for el in usando_docx_partition:
            text_in_docx_partition = text_in_docx_partition + " " + str(el)

        return text_in_docx_partition

    def get_text_from_xlsx(self, xlsx_file_route):
        if not xlsx_available:
            raise ImportError("xlsx is not available")

        # Hay que ver como hacer esto o como aprovechar la estructura xDD
        elements = partition_xlsx(filename=xlsx_file_route)
        result = ""
        for i, content in enumerate(elements):
            result += " " + elements[i].metadata.text_as_html

        return result

    def clean_text(self, text):
        """Pre-process text and generate tokens

        Args:
            text: Text to tokenize.

        Returns:
            Tokenized text.
        """
        text = str(text).lower()  # Lowercase words
        text = re.sub(r"\[(.*?)\]", "", text)  # Remove [+XYZ chars] in content
        text = re.sub(r"\s+", " ", text)  # Remove multiple spaces in content
        text = re.sub(r"\w+…|…", "", text)  # Remove ellipsis (and last word)
        text = re.sub(r"(?<=\w)-(?=\w)", " ", text)  # Replace dash between words
        text = re.sub(
            f"[{re.escape(string.punctuation)}]", "", text
        )  # Remove punctuation

        tokens = self.tokenizer(text)  # Get tokens from text
        tokens = [t for t in tokens if not t in self.stopwords]  # Remove stopwords
        tokens = ["" if t.isdigit() else t for t in tokens]  # Remove digits
        tokens = [t for t in tokens if len(t) > 1]  # Remove short tokens
        return tokens

    # Esta funcion podria ser util para caracterizar los documentos, recibe como input el output de un partioner
    def get_only_narrative_text(self, elements_format):
        text = ""
        for element in elements_format[: len(elements_format)]:
            if isinstance(element, NarrativeText) and sentence_count(element.text) > 2:
                text = text + " " + element
        return text

    # Observacion: En esta funcion el unico criterio para definir oraciones es la cantidad de tokens que la componen
    # por lo que podría perderse contexto. Otro approach podria ser el metodo get_chunks bajo este metodo
    def get_sentences(self, text, sentence_size):
        result = []
        texto = text.split(" ")
        i = 0
        n_tokens = len(texto)
        while i < n_tokens:
            if i + sentence_size < n_tokens:
                sentence = get_string_from_list(texto[i : i + sentence_size])
                result.append(sentence)
                i += sentence_size

            else:
                sentence = get_string_from_list(texto[i:n_tokens])
                result.append(sentence)
                break

        return result

    def get_chunks(self, text, chunk_size=1000):
        text_splitter = RecursiveCharacterTextSplitter(
            separators=[" ", ",", "\n"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_size / 5,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)

        return chunks

    # Función index_parser: devuelve un diccionario que tiene como llaves secciones del indice de un contrato, y su valor la pagina asociada a dicho valor
    # Recibe como input: el output de partition_pdf de "unstructured"
    def index_parser(self, contrato):
        list_index = []
        for i in range(0, int(len(contrato) / 4)):
            if "..." in str(contrato[i]):
                list_index.append(str(contrato[i]))

        for i in range(0, len(list_index)):
            list_index[i] = list_index[i].replace(".", "")

        dict_index = {}

        for seccion in list_index:
            list_seccion = seccion.split(" ")
            seccion_name = " ".join(
                [str(el) for el in list_seccion if str(el) != ""][
                    : len(list_seccion) - 2
                ]
            )

            dict_index[seccion_name] = int(list_seccion[-1])

        # Aqui es donde se pueden modificar los valores del indice
        # tambien habria que modificar la funcion para obtener la ultima pagina de la seccion
        # aca tambien se podria hacer un if siguiente seccion value == value de la actual seccion, entonces lo que viene son subsecciones?
        # Me pille que en vulco estan indexados sin contar portada como pagina (es decir, no se deben disminuir en 1 los valores)
        for key, value in dict_index.items():
            dict_index[key] = value - 1

        return dict_index

    # Recibe como input el output de partition_pdf de "unstructured"
    # El output es una lista con el contenido en texto del documento, cada elemento en la lista es una pagina
    def get_text_pages(self, contrato):
        len_document = contrato[-1].metadata.page_number
        pages_list = [None] * len_document
        for element in contrato:
            page_number = element.metadata.page_number
            if pages_list[page_number - 1] != None:
                pages_list[page_number - 1] += str(element)
            else:
                pages_list[page_number - 1] = str(element)
        return pages_list


diccionario_keywords = {
    "Alcance de Servicios": [
        "ALCANCE DE LOS SERVICIOS",
        "DESCRIPCIÓN DE LOS SERVICIOS",
        "SCOPE OF SERVICES",
        "alcance tecnico",
        "SCHEDULE – SCOPE OF SERVICES",
    ],
    "Vigencia del Contrato": [
        "fecha de acceso",
        "fecha de cumplimiento",
        "Especificaciones del contrato",
    ],
    "Terminación Anticipada": ["NO CONFORMIDADES", "Terminación Contrato"],
    "KPIs": ["INDICADORES CLAVE DE DESEMPEÑO", "Anexo", "Key Performance Indicators"],
}


levenshtain = textdistance.Levenshtein
# criteria es una clase de textdistance


def distance_words(word1, word2, criteria):
    distance = criteria(external=False)(word1, word2)
    return distance


def simple_embedding_cos_similarity(model, sentence1, sentence2):
    embedding_1 = model.encode(sentence1, convert_to_tensor=True)
    embedding_2 = model.encode(sentence2, convert_to_tensor=True)

    return util.pytorch_cos_sim(embedding_1, embedding_2)


def select_index_section(doc_index, q_set_name, criteria):
    """
    Given the question set and the document index, select the section that matches the question set.

    This runs a lexicographic similarity search between the question set name and the document index.
    """
    most_likely_section = None
    similarities = []
    query_names = diccionario_keywords[q_set_name]
    # Dado que tenemos el nombre de la query, obtenemos los posibles nombres
    # de secciones para poder realizar una busqueda por similaridad
    # A continuacion buscamos usando los posibles nombres de seccion, la seccion del documento que mejor matchee

    for section_name in query_names:
        for actual_section_name in doc_index.keys():
            # lexicographic similarity measure between the question set name and the section name
            # similarity = lexico_similarity(q_set_name, section_name)
            if criteria == "lexico":
                similarity = distance_words(
                    actual_section_name, section_name, levenshtain
                )
            elif criteria == "semantica":
                model = SentenceTransformer("hiiamsid/sentence_similarity_spanish_es")
                similarity = simple_embedding_cos_similarity(
                    model, actual_section_name, section_name
                )

            similarities.append((actual_section_name, similarity))

    # argmax of the similarities
    print(similarities)
    if criteria == "semantica":
        most_likely_section = max(similarities, key=lambda x: x[1])[0]
    else:
        most_likely_section = min(similarities, key=lambda x: x[1])[0]
    return most_likely_section
