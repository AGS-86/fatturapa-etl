import os
import shutil
import logging
import yaml

from src.extract_invoice import *
from src.transform import transform_invoice
from src.load_postgres import get_connection, load_invoice


# ----------------------------------
# Config & logging
# ----------------------------------

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(cfg):

    log_dir = cfg["logging"]["file_path"]      
    log_file = cfg["logging"]["log_file"]      
    log_path = os.path.join(log_dir, log_file) 

    # make dire if not exist!
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=cfg["logging"]["level"],
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )


# ----------------------------------
# Batch processing
# ----------------------------------

def process_invoices():
    cfg = load_config()
    setup_logging(cfg)

    invoices_dir = cfg["paths"]["invoices_dir"]
    archive_dir = cfg["paths"]["archive_dir"]
    error_dir = cfg["paths"]["error_dir"]
    company_vat = set(cfg["company_reference"]["vat_number"])

    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)

    conn = get_connection(cfg["database"])

    for filename in os.listdir(invoices_dir):
        if not filename.lower().endswith((".xml", ".p7m")):
            continue

        file_path = os.path.join(invoices_dir, filename)

        try:
            name_file, xml_bytes=convert_p7m(file_path)
            raw_data = read_invoice(name_file, xml_bytes)
            transformed = transform_invoice(raw_data,company_vat)

            load_invoice(conn, transformed)

            shutil.move(file_path, os.path.join(archive_dir, filename))
            logging.info(f"Processing {filename} - Successfully loaded")

        except Exception as e:
            logging.error(f"Processing {filename} - Error processing : {e}")
            shutil.move(file_path, os.path.join(error_dir, filename))

    conn.close()


if __name__ == "__main__":
    process_invoices()

