
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

def read_invoice(nome_file,file):


    # Se sono bytes → decodifica
    if isinstance(file, bytes):
        xml_string = file.decode("utf-8", errors="replace")
    # Se è una stringa già decodificata → usa direttamente
    elif isinstance(file, str):
        xml_string = str(file).encode("utf-8", errors="replace").decode("utf-8")
    else:
        raise TypeError("Tipo contenuto XML non supportato")

    # Parse XML
    tree = ET.ElementTree(ET.fromstring(xml_string))
    
    rif='Nome File:'+nome_file.split('/')[-1] #se funzia questo va cambiato

    root = tree.getroot()

    # Header
    header = root.find('.//FatturaElettronicaHeader')
    cedente = header.find('.//CedentePrestatore')
    committente = header.find('.//CessionarioCommittente')

    # Cedente Prestatore
    cedente_data = {
        'denominazione': cedente.findtext('.//Denominazione', ''),
        'partita_iva': cedente.findtext('.//IdCodice', ''),
        'codice_fiscale': cedente.findtext('.//CodiceFiscale', ''),
        'indirizzo': cedente.findtext('.//Indirizzo', ''),
        'cap': cedente.findtext('.//CAP', ''),
        'comune': cedente.findtext('.//Comune', ''),
        'provincia': cedente.findtext('.//Provincia', ''),
        'nazione': cedente.findtext('.//Nazione', ''),
        'telefono': cedente.findtext('.//Telefono', ''),
        'email': cedente.findtext('.//Email', ''),
    }

    # Cessionario Committente
    committente_data = {
        'denominazione': committente.findtext('.//Denominazione', ''),
        'partita_iva': committente.findtext('.//IdCodice', ''),
        'codice_fiscale': committente.findtext('.//CodiceFiscale', ''),
        'indirizzo': committente.findtext('.//Indirizzo', ''),
        'cap': committente.findtext('.//CAP', ''),
        'comune': committente.findtext('.//Comune', ''),
        'provincia': committente.findtext('.//Provincia', ''),
        'nazione': committente.findtext('.//Nazione', ''),
        'telefono': committente.findtext('.//Telefono', ''),
        'email': committente.findtext('.//Email', ''),
    }

    # Corpo Fattura
    body = root.find('.//FatturaElettronicaBody')
    dati_doc = body.find('.//DatiGeneraliDocumento')
    dati_contratti = body.findall('.//DatiContratto')
    dati_beni_servizi = body.find('.//DatiBeniServizi')
    dati_pagamento = body.find('.//DatiPagamento')
    allegati = body.findall('.//Allegati')

    # Dati Documento
    documento = {
        'tipo_documento': dati_doc.findtext('TipoDocumento', ''),
        'divisa': dati_doc.findtext('Divisa', ''),
        'data': dati_doc.findtext('Data', ''),
        'numero': dati_doc.findtext('Numero', ''),
        'importo_totale': dati_doc.findtext('ImportoTotaleDocumento', ''),
        'bollo_virtuale': dati_doc.findtext('.//BolloVirtuale', ''),
        'importo_bollo': dati_doc.findtext('.//ImportoBollo', ''),
        'causale': ' '.join([c.text for c in dati_doc.findall('Causale')]),
    }

    # Contratti
    contratti = []
    for c in dati_contratti:
        contratti.append({
            'id_documento': c.findtext('IdDocumento', ''),
            'codice_commessa': c.findtext('CodiceCommessaConvenzione', ''),
        })

    # Dettaglio Linee
    linee = []
    for dettaglio in dati_beni_servizi.findall('DettaglioLinee'):
        linee.append({
            'numero_linea': dettaglio.findtext('NumeroLinea', ''),
            'codice_articolo': dettaglio.findtext('.//CodiceValore', ''),
            'descrizione': dettaglio.findtext('Descrizione', ''),
            'quantita': dettaglio.findtext('Quantita', ''),
            'unita_misura': dettaglio.findtext('UnitaMisura', ''),
            'prezzo_unitario': dettaglio.findtext('PrezzoUnitario', ''),
            'prezzo_totale': dettaglio.findtext('PrezzoTotale', ''),
            'aliquota_iva': dettaglio.findtext('AliquotaIVA', ''),
            'natura': dettaglio.findtext('Natura', ''),
            'sconto_maggiorazione': dettaglio.findtext('Sconto/Maggiorazione', ''),
            'altri_dati_gestionali': [
                {
                    'tipo_dato': adg.findtext('TipoDato', ''),
                    'riferimento_testo': adg.findtext('RiferimentoTesto', '')
                }
                for adg in dettaglio.findall('AltriDatiGestionali')
            ]
        })

    # Riepilogo IVA
    vat_summary = []
    for riepilogo in dati_beni_servizi.findall('DatiRiepilogo'):
        vat_summary.append({
            'aliquota_iva': riepilogo.findtext('AliquotaIVA', ''),
            'natura': riepilogo.findtext('Natura', ''),
            'imponibile_importo': riepilogo.findtext('ImponibileImporto', ''),
            'imposta': riepilogo.findtext('Imposta', ''),
            'riferimento_normativo': riepilogo.findtext('RiferimentoNormativo', ''),
        })

    # Pagamento
    payments = {
        'condizioni_pagamento': dati_pagamento.findtext('CondizioniPagamento', ''),
        'modalita_pagamento': dati_pagamento.findtext('.//ModalitaPagamento', ''),
        'data_scadenza': dati_pagamento.findtext('.//DataScadenzaPagamento', ''),
        'importo_pagamento': dati_pagamento.findtext('.//ImportoPagamento', ''),
        'iban': dati_pagamento.findtext('.//IBAN', ''),
        'beneficiario': dati_pagamento.findtext('.//Beneficiario', ''),
    }

    # Allegati
    allegati_data = []
    for a in allegati:
        allegati_data.append({
            'nome': a.findtext('NomeAttachment', ''),
            'formato': a.findtext('FormatoAttachment', ''),
            'contenuto': a.findtext('Attachment', ''),
        })

    # Risultato finale
    fattura = {
        'cedente': cedente_data,
        'committente': committente_data,
        'documento': documento,
        'contratti': contratti,
        'linee': linee,
        'riepilogo_iva': vat_summary,
        'pagamento': payments,
#        'allegati': allegati_data,
    }

    return fattura

'''
file="../errors/IT00463660399_5QJAF.xml"
#file="../invoices/IT05006900962_aivdn.xml"
nome_file,new_file=convert_p7m(file)
f=read_invoice(nome_file,new_file)

print(f)
'''