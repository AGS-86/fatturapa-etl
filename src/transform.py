from datetime import datetime
from decimal import Decimal


def to_decimal(value):
    if value in (""," ", None):
        return 0
    return Decimal(str(value).replace(",", "."))


def to_date(value):
    if not value:
        return None
    elif len(value) >= 10 and value[4] == "-" and value[7] == "-":
        head = value[:10]
        try:
            return datetime.strptime(head, "%Y-%m-%d").date()
        except ValueError:
            return None

def normalize_string(value):
    return value.strip() if isinstance(value, str) else None


# -----------------------------
# Normalizzazione aziende
# -----------------------------

def normalize_company(company: dict) -> dict:
    return {
        "denominazione": normalize_string(company.get("denominazione")),
        "partita_iva": normalize_string(company.get("partita_iva")),
        "codice_fiscale": normalize_string(company.get("codice_fiscale")),
        "indirizzo": normalize_string(company.get("indirizzo")),
        "cap": normalize_string(company.get("cap")),
        "comune": normalize_string(company.get("comune")),
        "provincia": normalize_string(company.get("provincia")),
        "nazione": normalize_string(company.get("nazione")),
        "telefono": normalize_string(company.get("telefono")),
        "email": normalize_string(company.get("email")),
    }


# -----------------------------
# Normalizzazione documento
# -----------------------------

def normalize_invoice(documento: dict) -> dict:
    return {
        "tipo_documento": normalize_string(documento.get("tipo_documento")),
        "divisa": normalize_string(documento.get("divisa")),
        "data": to_date(documento.get("data")),
        "numero": normalize_string(documento.get("numero")),
        "importo_totale": to_decimal(documento.get("importo_totale")),
        "bollo_virtuale": normalize_string(documento.get("bollo_virtuale")),
        "importo_bollo": to_decimal(documento.get("importo_bollo")),
        "causale": normalize_string(documento.get("causale")),
    }


# -----------------------------
# Normalizzazione linee
# -----------------------------

def normalize_lines(lines: list) -> list:
    normalized = []

    for line in lines:
        normalized.append({
            "numero_linea": int(line.get("numero_linea")),
            "codice_articolo": normalize_string(line.get("codice_articolo")),
            "descrizione": normalize_string(line.get("descrizione")),
            "quantita": to_decimal(line.get("quantita")),
            "unita_misura": normalize_string(line.get("unita_misura")),
            "prezzo_unitario": to_decimal(line.get("prezzo_unitario")),
            "prezzo_totale": to_decimal(line.get("prezzo_totale")),
            "aliquota_iva": to_decimal(line.get("aliquota_iva")),
            "natura": normalize_string(line.get("natura")),
            "sconto_maggiorazione": to_decimal(line.get("sconto_maggiorazione")),
        })

    return normalized

def normalize_vat_summary(riepilogo_iva: list) -> list:
    normalized = []

    for line in riepilogo_iva:
        normalized.append({
        'aliquota_iva': to_decimal(line.get("aliquota_iva")),
        'natura': normalize_string(line.get("natura")),
        'imponibile_importo': to_decimal(line.get("imponibile_importo")),
        'imposta': to_decimal(line.get("imposta")),
        'riferimento_normativo': normalize_string(line.get("riferimento_normativo")),
    })
    return normalized
def normalize_payments(pagamento: dict) -> dict:
    return {
        'condizioni_pagamento': normalize_string(pagamento.get("condizioni_pagamento")),
        'modalita_pagamento': normalize_string(pagamento.get("modalita_pagamento")),
        'data_scadenza': to_date(pagamento.get("data_scadenza")),
        'importo_pagamento': normalize_string(pagamento.get("importo_pagamento")),
        'iban': normalize_string(pagamento.get("iban")),
        'beneficiario': normalize_string(pagamento.get("beneficiario")),
    }


# -----------------------------
# Normalizzazione completa
# -----------------------------
def determine_invoice_type(cedente: dict, committente: dict, piva_azienda: set) -> str:
    if cedente.get("partita_iva") in piva_azienda:
        return "attiva"
    elif committente.get("partita_iva") in piva_azienda:
        return "passiva"
    else:
        raise ValueError("Impossibile determinare il tipo di fattura")

def transform_invoice(invoice_data: dict, company_vat: set) -> dict:
    cedente = normalize_company(invoice_data["cedente"])
    committente = normalize_company(invoice_data["committente"])

    invoice_type = determine_invoice_type(
        cedente,
        committente,
        company_vat
    )

    documento = normalize_invoice(invoice_data["documento"])
    documento["invoice_type"] = invoice_type

    return {
        "cedente": cedente,
        "committente": committente,
        "documento": documento,
        "linee": normalize_lines(invoice_data.get("linee", [])),
        "riepilogo_iva": normalize_vat_summary(invoice_data.get("riepilogo_iva",[])),
        "pagamento": normalize_payments(invoice_data.get("pagamento")),
    }
