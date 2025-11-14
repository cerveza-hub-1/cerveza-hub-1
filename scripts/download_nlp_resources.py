"""
Script de post-instalación para descargar recursos de PLN.

Este script descarga los corpus necesarios de NLTK (como 'stopwords', 'wordnet')
y los modelos de spaCy ('en_core_web_sm', 'es_core_web_sm') para evitar
errores 'LookupError' al iniciar la aplicación Flask.
"""

import subprocess
import sys
import nltk


NLTK_RESOURCES = [
    'stopwords',
    'punkt',
    'punkt_tab',
    'wordnet',
    'omw-1.4',
    'averaged_perceptron_tagger',
    'averaged_perceptron_tagger_eng'
]

SPACY_MODELS = ["en_core_web_sm"]


def download_nltk_resources():
    """
    Descarga los corpus y tokenizadores necesarios de NLTK.
    Evita el error 'LookupError: Resource stopwords not found'.
    """
    print("Iniciando descarga de recursos NLTK...")

    for resource in NLTK_RESOURCES:
        try:
            print(f"Verificando/Descargando '{resource}'...")
            nltk.download(resource, quiet=True)
            print(f"'{resource}' listo.")
        except Exception as e:
            print(f"Error descargando '{resource}': {type(e).__name__} - {e}")

def download_spacy_models():
    """
    Descarga los modelos lingüísticos de spaCy para inglés y español
    usando subprocess para llamar al comando nativo de Python.
    Esto equivale a ejecutar 'python -m spacy download <modelo>'.
    """
    print("\nIniciando descarga de modelos spaCy...")

    for model in SPACY_MODELS:
        try:
            print(f"Instalando modelo spaCy '{model}'...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", model])
            print(f"Modelo '{model}' instalado correctamente.")
        except subprocess.CalledProcessError:
             print(f"Falló la instalación automática de '{model}'.")
             print(f"Intenta ejecutar manualmente: python -m spacy download {model}")
        except Exception as e:
            print(f"Error inesperado instalando '{model}': {type(e).__name__} - {e}")

def main():
    """
    Punto de entrada principal del script.
    Ejecuta la descarga de NLTK y spaCy.
    """
    print("========================================")
    print("Configurando entorno de PLN (NLTK + spaCy)")
    print("========================================\n")

    try:
        download_nltk_resources()

        download_spacy_models()

        print("\n========================================")
        print("¡Configuración de PLN completada!")
        print("Ahora puedes ejecutar 'flask run' sin errores de recursos.")
        print("========================================")

    except KeyboardInterrupt:
        print("\n\n Instalación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n Ocurrió un error crítico durante la configuración: {type(e).__name__} - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()