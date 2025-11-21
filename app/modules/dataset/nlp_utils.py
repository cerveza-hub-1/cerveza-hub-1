import re
import warnings
from collections import Counter
from typing import List

import contractions
import spacy
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

nlp = spacy.load("en_core_web_sm")

palabras_vacias_ingles = set(stopwords.words("english"))

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)


def elimina_html(contenido: str) -> str:
    """Elimina etiquetas HTML del contenido."""
    return BeautifulSoup(contenido, "html.parser").get_text()


def expandir_contracciones(contenido: str) -> str:
    """Expande contracciones (e.g., I'm -> I am)."""
    return contractions.fix(contenido)


def pasar_a_minuscula(contenido: str) -> str:
    """Convierte el texto a minúsculas."""
    return contenido.lower()


def limpiar_texto(texto: str) -> str:
    """Elimina caracteres no alfabéticos y espacios extra."""
    texto = re.sub(r"[^a-zA-Z\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def elimina_no_alfanumerico(contenido: List[str]) -> List[str]:
    """Elimina tokens no alfanuméricos."""
    return [re.sub(r"[^\w]", "", palabra) for palabra in contenido if re.search(r"\w", palabra)]


def elimina_palabras_vacias(contenido: List[str]) -> List[str]:
    """Elimina palabras vacías (stopwords) usando la lista unificada (inglés + español)."""
    return [palabra for palabra in contenido if palabra not in palabras_vacias_ingles]


def lematizador(contenido: List[str]) -> List[str]:
    """Aplica lematización a los tokens, priorizando verbos."""
    lemmatizer = WordNetLemmatizer()
    pos_tags = pos_tag(contenido)
    resultado = []

    for palabra, tag in pos_tags:
        if tag.startswith("VB"):  
            resultado.append(lemmatizer.lemmatize(palabra, pos="v"))
        else:
            resultado.append(palabra)

    return resultado


def expand_term(term: str) -> set:
    """Encuentra sinónimos de un término usando WordNet."""
    related = set()
    for syn in wn.synsets(term):
        for lemma in syn.lemmas():
            word = lemma.name().replace("_", " ").lower()
            if word != term:
                related.add(word)
    return related


def expand_corpus_with_synonyms(documento: List[str]) -> List[str]:
    """Expande el documento con sinónimos de cada palabra."""
    doc_counter = Counter(documento)
    expanded_doc = []

    for word, count in doc_counter.items():
        # Añadir la palabra original las veces que aparece
        expanded_doc.extend([word] * count)
        synonyms = expand_term(word)
        for syn in synonyms:
            # Ponderar los sinónimos igual que la palabra original (para TF-IDF)
            expanded_doc.extend([syn] * count)

    return expanded_doc


def proceso_contenido_completo(texto: str) -> str:
    """
    Aplica todo el pipeline de procesamiento de texto (limpieza, normalización,
    lematización, noun chunks y expansión de sinónimos) y devuelve una cadena
    preparada para TF-IDF.
    """

    texto = elimina_html(texto)
    texto = expandir_contracciones(texto)
    texto = pasar_a_minuscula(texto)
    texto = limpiar_texto(texto)
    tokens = word_tokenize(texto)

    tokens = elimina_no_alfanumerico(tokens)
    tokens = elimina_palabras_vacias(tokens)
    tokens = lematizador(tokens)

    tokens = expand_corpus_with_synonyms(tokens)

    return " ".join(tokens)