
import xml.etree.ElementTree as ET

from asn1crypto import cms

def convert_p7m(file):
    est = file.split('.')[-1].lower()
    nome_file = file

    # Se NON è p7m → ritorna contenuto così com'è (per esempio XML normale)
    if est != "p7m":
        with open(file, "rb") as f:
            return nome_file, f.read()

    # Lettura del file p7m
    with open(file, "rb") as f:
        p7m_bytes = f.read()

    try:
        content_info = cms.ContentInfo.load(p7m_bytes)

        # Deve essere SignedData
        if content_info['content_type'].native != 'signed_data':
            raise ValueError("Il file non contiene SignedData")

        signed_data = content_info['content']

        # Questa è la parte XML "incapsulata" dentro la busta p7m
        payload = signed_data['encap_content_info']['content'].native

        # payload è in bytes (l'XML originale)
        return nome_file, payload

    except Exception as e:
        # In caso di errore → ritorno il file originale
        return nome_file, p7m_bytes

def safe_findtext(elem, path, default=None):
    return elem.findtext(path, default) if elem is not None else default

def read_invoice(nome_file, file):
    import xml.etree.ElementTree as ET

    # Decodifica file
    if isinstance(file, bytes):
        xml_string = file.decode("utf-8", errors="replace")
    elif isinstance(file, str):
        xml_string = str(file).encode("utf-8", errors="replace").decode("utf-8")
    else:
        raise TypeError("Tipo contenuto XML non supportato")

    tree = ET.ElementTree(ET.fromstring(xml_string))
    root = tree.getroot()

    # Header
    header = root.find('.//FatturaElettronicaHeader')
    cedente = header.find('.//CedentePrestatore') if header is not None else None
    committente = header.find('.//CessionarioCommittente') if header is not None else None

    cedente_data = {
        'denominazione': safe_findtext(cedente, './/Denominazione'),
        'partita_iva': safe_findtext(cedente, './/IdCodice'),
        'codice_fiscale': safe_findtext(cedente, './/CodiceFiscale'),
        'indirizzo': safe_findtext(cedente, './/Indirizzo'),
        'cap': safe_findtext(cedente, './/CAP'),
        'comune': safe_findtext(cedente, './/Comune'),
        'provincia': safe_findtext(cedente, './/Provincia'),
        'nazione': safe_findtext(cedente, './/Nazione'),
        'telefono': safe_findtext(cedente, './/Telefono'),
        'email': safe_findtext(cedente, './/Email'),
    }

    committente_data = {
        'denominazione': safe_findtext(committente, './/Denominazione'),
        'partita_iva': safe_findtext(committente, './/IdCodice'),
        'codice_fiscale': safe_findtext(committente, './/CodiceFiscale'),
        'indirizzo': safe_findtext(committente, './/Indirizzo'),
        'cap': safe_findtext(committente, './/CAP'),
        'comune': safe_findtext(committente, './/Comune'),
        'provincia': safe_findtext(committente, './/Provincia'),
        'nazione': safe_findtext(committente, './/Nazione'),
        'telefono': safe_findtext(committente, './/Telefono'),
        'email': safe_findtext(committente, './/Email'),
    }

    # Corpo Fattura
    body = root.find('.//FatturaElettronicaBody')
    dati_doc = body.find('.//DatiGeneraliDocumento') if body is not None else None
    dati_contratti = body.findall('.//DatiContratto') if body is not None else []
    dati_beni_servizi = body.find('.//DatiBeniServizi') if body is not None else None
    dati_pagamento = body.find('.//DatiPagamento') if body is not None else None
    allegati = body.findall('.//Allegati') if body is not None else []

    documento = {
        'tipo_documento': safe_findtext(dati_doc, 'TipoDocumento'),
        'divisa': safe_findtext(dati_doc, 'Divisa'),
        'data': safe_findtext(dati_doc, 'Data'),
        'numero': safe_findtext(dati_doc, 'Numero'),
        'importo_totale': safe_findtext(dati_doc, 'ImportoTotaleDocumento'),
        'bollo_virtuale': safe_findtext(dati_doc, './/BolloVirtuale'),
        'importo_bollo': safe_findtext(dati_doc, './/ImportoBollo'),
        'causale': ' '.join([c.text or "" for c in dati_doc.findall('Causale')]) if dati_doc is not None else '',
    }

    contratti = []
    for c in dati_contratti or []:
        contratti.append({
            'id_documento': safe_findtext(c, 'IdDocumento'),
            'codice_commessa': safe_findtext(c, 'CodiceCommessaConvenzione'),
        })

    linee = []
    if dati_beni_servizi is not None:
        for dettaglio in dati_beni_servizi.findall('DettaglioLinee'):
            linee.append({
                'numero_linea': safe_findtext(dettaglio, 'NumeroLinea'),
                'codice_articolo': safe_findtext(dettaglio, './/CodiceValore'),
                'descrizione': safe_findtext(dettaglio, 'Descrizione'),
                'quantita': safe_findtext(dettaglio, 'Quantita'),
                'unita_misura': safe_findtext(dettaglio, 'UnitaMisura'),
                'prezzo_unitario': safe_findtext(dettaglio, 'PrezzoUnitario'),
                'prezzo_totale': safe_findtext(dettaglio, 'PrezzoTotale'),
                'aliquota_iva': safe_findtext(dettaglio, 'AliquotaIVA'),
                'natura': safe_findtext(dettaglio, 'Natura'),
                'sconto_maggiorazione': safe_findtext(dettaglio, 'Sconto/Maggiorazione'),
                'altri_dati_gestionali': [
                    {
                        'tipo_dato': safe_findtext(adg, 'TipoDato'),
                        'riferimento_testo': safe_findtext(adg, 'RiferimentoTesto')
                    }
                    for adg in dettaglio.findall('AltriDatiGestionali')
                ]
            })

    vat_summary = []
    if dati_beni_servizi is not None:
        for riepilogo in dati_beni_servizi.findall('DatiRiepilogo'):
            vat_summary.append({
                'aliquota_iva': safe_findtext(riepilogo, 'AliquotaIVA'),
                'natura': safe_findtext(riepilogo, 'Natura'),
                'imponibile_importo': safe_findtext(riepilogo, 'ImponibileImporto'),
                'imposta': safe_findtext(riepilogo, 'Imposta'),
                'riferimento_normativo': safe_findtext(riepilogo, 'RiferimentoNormativo'),
            })

    payments = {
        'condizioni_pagamento': safe_findtext(dati_pagamento, 'CondizioniPagamento'),
        'modalita_pagamento': safe_findtext(dati_pagamento, './/ModalitaPagamento'),
        'data_scadenza': safe_findtext(dati_pagamento, './/DataScadenzaPagamento'),
        'importo_pagamento': safe_findtext(dati_pagamento, './/ImportoPagamento'),
        'iban': safe_findtext(dati_pagamento, './/IBAN'),
        'beneficiario': safe_findtext(dati_pagamento, './/Beneficiario'),
    }

    allegati_data = []
    for a in allegati or []:
        allegati_data.append({
            'nome': safe_findtext(a, 'NomeAttachment'),
            'formato': safe_findtext(a, 'FormatoAttachment'),
            'contenuto': safe_findtext(a, 'Attachment'),
        })

    fattura = {
        'cedente': cedente_data,
        'committente': committente_data,
        'documento': documento,
        'contratti': contratti,
        'linee': linee,
        'riepilogo_iva': vat_summary,
        'pagamento': payments,
        # 'allegati': allegati_data,
    }

    return fattura

