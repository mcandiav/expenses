import re
import unicodedata


def normalizar_glosa(glosa: str) -> str:
    if not glosa:
        return ""
    texto = glosa.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()
