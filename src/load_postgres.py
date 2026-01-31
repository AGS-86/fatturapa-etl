import psycopg2
from psycopg2.extras import execute_values


# ----------------------------------
# Connessione
# ----------------------------------

def get_connection(config: dict):
    return psycopg2.connect(
        dbname=config["db_name"],
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
    )


# ----------------------------------
# UPSERT azienda
# ----------------------------------

def upsert_company(cur, company: dict) -> int:
    """
    Inserisce azienda se non esiste, altrimenti ritorna l'id esistente
    """
    query = """
    INSERT INTO companies (
        denominazione, partita_iva, codice_fiscale,
        indirizzo, cap, comune, provincia, nazione,
        telefono, email
    )
    VALUES (%(denominazione)s, %(partita_iva)s, %(codice_fiscale)s,
            %(indirizzo)s, %(cap)s, %(comune)s, %(provincia)s, %(nazione)s,
            %(telefono)s, %(email)s)
    ON CONFLICT (partita_iva)
    DO UPDATE SET denominazione = EXCLUDED.denominazione
    RETURNING company_id;
    """
    cur.execute(query, company)
    return cur.fetchone()[0]


# ----------------------------------
# Inserimento fattura
# ----------------------------------

def insert_invoice(cur, invoice: dict, id_cedente: int, id_committente: int) -> int:
    query = """
    INSERT INTO invoices (
        tipo_documento, divisa, data_documento,
        numero_documento, importo_totale,
        bollo_virtuale, importo_bollo, causale, invoice_type,
        cedente_id, committente_id

    )
    VALUES (
        %s, %s, %s, %s, %s,%s,
        %s, %s, %s, %s, %s
    )
    RETURNING invoice_id;
    """

    cur.execute(
        query,
        (
            invoice["tipo_documento"],
            invoice["divisa"],
            invoice["data"],
            invoice["numero"],
            invoice["importo_totale"],
            invoice["bollo_virtuale"],
            invoice["importo_bollo"],
            invoice["causale"],
            invoice["invoice_type"],
            id_cedente,
            id_committente,
        ),
    )
    return cur.fetchone()[0]


# ----------------------------------
# Inserimento righe fattura
# ----------------------------------

def insert_lines(cur, id_invoice: int, lines: list):
    query = """
    INSERT INTO invoice_lines (
        invoice_id, numero_linea, codice_articolo,
        descrizione, quantita, unita_misura,prezzo_unitario,
        prezzo_totale, aliquota_iva, natura, sconto_maggiorazione
    )
    VALUES %s;
    """

    values = [
        (
            id_invoice,
            l["numero_linea"],
            l["codice_articolo"],
            l["descrizione"],
            l["quantita"],
            l["unita_misura"],
            l["prezzo_unitario"],
            l["prezzo_totale"],
            l["aliquota_iva"],
            l["natura"],
            l["sconto_maggiorazione"],
        )
        for l in lines
    ]

    execute_values(cur, query, values)


# ----------------------------------
# Inserimento riepilogo IVA
# ----------------------------------

def insert_vat_summary(cur, id_invoice: int, vat_rows: list):
    query = """
    INSERT INTO vat_summary (
        invoice_id, aliquota_iva, natura,
        imponibile_importo, imposta, riferimento_normativo
    )
    VALUES %s;
    """

    values = [
        (
            id_invoice,
            v["aliquota_iva"],
            v["natura"],
            v["imponibile_importo"],
            v["imposta"],
            v["riferimento_normativo"],
        )
        for v in vat_rows
    ]

    execute_values(cur, query, values)


# ----------------------------------
# Inserimento pagamento
# ----------------------------------

def insert_payment(cur, id_invoice: int, payment: dict):
    if not payment:
        return

    query = """
    INSERT INTO payments (
        invoice_id, condizioni_pagamento, modalita_pagamento,
        data_scadenza, importo_pagamento, iban, beneficiario
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """

    cur.execute(
        query,
        (
            id_invoice,
            payment.get("condizioni_pagamento"),
            payment.get("modalita_pagamento"),
            payment.get("data_scadenza"),
            payment.get("importo_pagamento"),
            payment.get("iban"),
            payment.get("beneficiario"),
        ),
    )


# ----------------------------------
# LOAD COMPLETO
# ----------------------------------

def load_invoice(conn, transformed: dict):
    with conn:
        with conn.cursor() as cur:
            id_cedente = upsert_company(cur, transformed["cedente"])
            id_committente = upsert_company(cur, transformed["committente"])

            id_invoice = insert_invoice(
                cur,
                transformed["documento"],
                id_cedente,
                id_committente,
            )

            insert_lines(cur, id_invoice, transformed["linee"])
            insert_vat_summary(cur, id_invoice, transformed.get("riepilogo_iva", []))
            insert_payment(cur, id_invoice, transformed.get("pagamento"))

