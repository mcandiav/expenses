import csv
import io
import zipfile
from enum import Enum


class FormatoArchivo(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    XLSX_OOXML = "xlsx_ooxml"
    XLS_BINARIO = "xls_binario"
    DESCONOCIDO = "desconocido"


PDF_MAGIC = b"%PDF"
OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP_MAGIC = b"PK"


def detectar_formato(content: bytes, nombre_archivo: str) -> FormatoArchivo:
    if not content:
        return FormatoArchivo.DESCONOCIDO

    if content.startswith(PDF_MAGIC):
        return FormatoArchivo.PDF

    if content.startswith(ZIP_MAGIC):
        return FormatoArchivo.XLSX_OOXML

    if content.startswith(OLE_MAGIC):
        return FormatoArchivo.XLS_BINARIO

    extension = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else ""
    if extension == "csv" or _parece_csv(content):
        return FormatoArchivo.CSV

    return FormatoArchivo.DESCONOCIDO


def _parece_csv(content: bytes) -> bool:
    muestra = content[:4096]
    for encoding in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            texto = muestra.decode(encoding)
        except UnicodeDecodeError:
            continue
        if not texto.strip():
            continue
        try:
            dialect = csv.Sniffer().sniff(texto, delimiters=",;\t|")
            reader = csv.reader(io.StringIO(texto), dialect)
            filas = [fila for fila in reader if any(celda.strip() for celda in fila)]
            return len(filas) >= 2 and len(filas[0]) >= 2
        except csv.Error:
            continue
    return False


def es_ooxml_zip(content: bytes) -> bool:
    if not content.startswith(ZIP_MAGIC):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            return "[Content_Types].xml" in zf.namelist()
    except zipfile.BadZipFile:
        return False
