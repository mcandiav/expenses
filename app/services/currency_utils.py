import re

MONEDAS_SOPORTADAS = ("CLP", "USD", "EUR")

MONEDA_PATTERNS = (
    (re.compile(r"\(\s*usd\s*\)|\busd\b", re.I), "USD"),
    (re.compile(r"\(\s*eur\s*\)|\beur\b", re.I), "EUR"),
    (re.compile(r"\(\s*clp\s*\)|\bclp\b", re.I), "CLP"),
)


def moneda_desde_texto(texto: str) -> str | None:
    for patron, codigo in MONEDA_PATTERNS:
        if patron.search(texto):
            return codigo
    return None


def inferir_moneda_archivo(nombre_archivo: str, subtipo_fuente: str | None) -> str:
    nombre = nombre_archivo.lower()
    subtipo = (subtipo_fuente or "").lower()
    if "internacional" in nombre or "internacional" in subtipo:
        return "USD"
    if "nacional" in nombre or "nacional" in subtipo:
        return "CLP"
    return "CLP"


def parse_monto(valor: str | None) -> float | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or texto.lower() == "none":
        return None
    negativo = texto.startswith("-") or texto.startswith("(")
    limpio = re.sub(r"[^\d,.\-]", "", texto)
    if "," in limpio and "." in limpio:
        if limpio.rfind(",") > limpio.rfind("."):
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "," in limpio:
        partes = limpio.split(",")
        limpio = limpio.replace(",", ".") if len(partes[-1]) <= 2 else limpio.replace(",", "")
    try:
        monto = float(limpio)
        return -abs(monto) if negativo else monto
    except ValueError:
        return None


def extraer_monto_y_moneda(
    data: dict,
    nombre_archivo: str = "",
    subtipo_fuente: str | None = None,
) -> tuple[float | None, str, str | None]:
    """Retorna (monto, moneda, columna_origen)."""
    respaldo: tuple[float | None, str, str | None] | None = None

    for clave, valor in data.items():
        clave_l = clave.lower()
        if not any(k in clave_l for k in ("monto", "importe", "amount", "cargo", "abono", "valor")):
            continue

        monto = parse_monto(str(valor).strip() if valor is not None else None)
        if monto is None:
            continue

        moneda_col = moneda_desde_texto(clave)
        if moneda_col:
            return monto, moneda_col, clave

        if respaldo is None:
            respaldo = (monto, inferir_moneda_archivo(nombre_archivo, subtipo_fuente), clave)

    if respaldo:
        return respaldo

    default = inferir_moneda_archivo(nombre_archivo, subtipo_fuente)
    return None, default, None
