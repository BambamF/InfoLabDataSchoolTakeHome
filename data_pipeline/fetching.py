import os
from dotenv import load_dotenv, find_dotenv
import requests
import logging
import pandas as pd
from .rate_limiter import RateLimiter
from typing import Callable, Any, Optional
from threading import Lock
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv(find_dotenv())

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(ROOT_DIR, 'data')

LOG_DIR = os.path.join(ROOT_DIR, 'logging')

COMPANIES_HOUSE_KEY = os.getenv("COMPANIES_HOUSE_KEY")

CSV_SAVE_PATH = os.path.join(DATA_DIR, 'matched_companies.csv')

rate_limiter = RateLimiter(60)

runtime_comp_path = os.path.join(DATA_DIR, 'runtime_comparison.csv')

companies_df = pd.read_csv(os.path.join(DATA_DIR, 'gamesmap.csv'))

companies = companies_df["name"].to_list()
company_numbers = companies_df["company_number"].to_list()
companies_dict = dict(zip(companies_df["company_number"], companies_df["name"]))

search_map = {
"APHA_SEARCH_URL": ("https://api.company-information.service.gov.uk/alphabetical-search/companies", "company_name"),
"ADVANCED_SEARCH_URL": ("https://api.company-information.service.gov.uk/advanced-search/companies", "company_name"),
"SEARCH_URL": ("https://api.company-information.service.gov.uk/search/companies", "title")
}

PROFILE_URL = "https://api.company-information.service.gov.uk/company/{}"

MAX_WORKERS = 6

HIGH_CONFIDENCE = 95
MEDIUM_CONFIDENCE = 80
LOW_CONFIDENCE = 50
GAP = 8

base_fieldnames = ["company_name", "company_number", "company_status", "company_type",
                   "date_of_creation", "date_of_cessation", "description", "persons_with_significant_control", 
                   "previous_company_names", "registered_office_address", "service_address", "sic_codes"]

mutex = Lock()
session = requests.Session()

def download_row(end_point: str, params: Optional[dict[str, Any]] = None, timeout: int = 30) -> Optional[dict]:
    retry = 1.0

    if COMPANIES_HOUSE_KEY is None:
        print(f"Error: COMPANIES_HOUSE_KEY is not configured")
        return None
    
    for i in range(5):
        rate_limiter.acquire()
        try:
            response = requests.get(end_point, params=params, auth=(COMPANIES_HOUSE_KEY, ""), timeout=timeout)
        except Exception as e:
            print(f"[DOWNLOAD_ROW] Exception encountered: {str(e)} | Retry: {retry} | Turn: {i} | URL: {os.path.basename(end_point)}")
            logging.exception(f"[DOWNLOAD_ROW] Exception encountered: {str(e)} | Retry: {retry} | Turn: {i} | URL: {os.path.basename(end_point)}")
            time.sleep(retry)
            retry *= 2
            continue

        if response.status_code == 429:
            retry_time = float(response.headers.get("Retry-After", retry))
            print(f"[DOWNLOAD_ROW] Error encountered | Status Code: {response.status_code} | Retry: {retry_time} | Turn: {i} | URL: {os.path.basename(end_point)}")
            logging.error(f"[DOWNLOAD_ROW] Error encountered | Status Code: {response.status_code} | Retry: {retry_time} | Turn: {i} | URL: {os.path.basename(end_point)}")
            time.sleep(retry_time)
            retry *= 2
            continue

        if response.status_code == 404:
            print(f"[DOWNLOAD_ROW] Error encountered | Status Code: {response.status_code} | URL: {os.path.basename(end_point)}")
            logging.error(f"[DOWNLOAD_ROW] Error encountered | Status Code: {response.status_code} | URL: {os.path.basename(end_point)}")
            continue

        response.raise_for_status()
        return response.json()

def get_company_name(candidate: dict) -> str:
    name = candidate.get('title') or candidate.get('company_name') or ''
    return str(name).strip()

def fetch_profile(company_number: str) -> Optional[dict]:
    return download_row(PROFILE_URL.format(company_number))

def format_address(address: dict[str, str]) -> str:
    if not address:
        return ""

    parts = [
        address.get("premises"), address.get("address_line_1"),
        address.get("address_line_2"), address.get("locality"),
        address.get("region"), address.get("postal_code"),
        address.get("country")
    ]
    return ", ".join(p for p in parts if p)

def format_previous_names(profile: dict) -> str:
    prev_names = profile.get("previous_company_names", [])
    formatted = []
    for p in prev_names:
        name = p.get("name", "")
        ceased = p.get("ceased_on", "")
        formatted.append(f"{name} (until {ceased})"  if ceased else name)
    return "; ".join(formatted)

def format_sic_codes(profile: dict) -> str:
    return "; ".join(profile.get("sic_codes", []))

def build_row(company_number: str) -> dict[str, Any] | None:
    base_row = {f: "" for f in base_fieldnames}
    try:
        company_profile: dict[str, Any] | None = fetch_profile(company_number) if company_number else None
        if company_profile:
            for f in base_fieldnames:
                base_row[f] = company_profile.get(f, "")
            base_row["registered_office_address"] = format_address(company_profile.get("registered_office_address", ""))
            base_row["service_address"] = format_address(company_profile.get("service_address", ""))
            base_row["sic_codes"] = format_sic_codes(company_profile)
            base_row["company_type"] = company_profile.get("type", "")
        else:
            return None
        logging.info(f"[BUILD ROW] Row Built | Company Number: {company_number} | Company Name: {base_row.get("company_name")}")
        return base_row
    except Exception as e:
        logging.exception(f"[BUILD ROW] Lookup Failed | Company Number: {company_number} | Company Name: {companies_dict.get(company_number, '')}")

def add_record_to_csv(row: dict[str, Any], csv_path: str):
    with mutex:
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, 'a', newline="", encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=base_fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        logging.info(f"[ADD RECORD TO CSV] Record added to csv | CSV Path: {os.path.basename(csv_path)} | Row: {str(row)}")

def raw_data_fetch(raw_data_csv_path: str, raw_data_log_path: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(filename=raw_data_log_path, 
                            format="%(asctime)s | %(message)s",
                            level=logging.INFO)
    processed_companies: set[str] = set()
    file_exists = os.path.isfile(raw_data_csv_path)
    if file_exists:
        print(f"Existing output file found at: {os.path.basename(raw_data_csv_path)}, reading checkpoints....")
        try:
            with open(raw_data_csv_path, 'a', encoding='utf-8', newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    for csv_row in header:
                        if csv_row and len(csv_row) > 0:
                            processed_companies.add(csv_row[0].strip())
            print(f"Checkpoint loaded, bypassing {len(processed_companies)} completed companies")
        except Exception as e:
            print(f"Failed to parse checkpoint safely: {str(e)}. Starting fresh...")
            file_exists = False

    if not file_exists or os.stat(raw_data_csv_path).st_size == 0:
        with open(raw_data_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=base_fieldnames)
            writer.writeheader()

    with open(raw_data_log_path, 'a', encoding='utf-8', newline='') as log_file:
        df = pd.read_csv(raw_data_csv_path)
        raw_names = [str(n).strip() for n in df['company_name'] if str(n).strip() and str(n).lower() != 'nan']
        todo_names = [name for name in raw_names if name not in processed_companies]

        skipped_count = len(raw_names) - len(todo_names)
        if skipped_count > 0:
            print(f"[RAW FETCH] Bypassing {skipped_count} items (already exist in checkpoint).")

        print(f"[RAW FETCH] Queueing {len(todo_names)} new companies across threadpool...")

        print()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_profile, company_number): company_number for company_number in company_numbers}
            for future in as_completed(futures):
                company_number = futures[future]
                try:
                    row = future.result()
                    if row:
                        add_record_to_csv(row, raw_data_csv_path)
                        print(f"[RAW FETCH EXECUTOR] {companies_dict.get(company_number, company_number)} -> Done.")
                        logging.info(f"[RAW FETCH EXECUTOR] {companies_dict.get(company_number, company_number)} -> Done.")
                    else:
                        print(f"[RAW FETCH EXECUTOR] No row found, exception encountered, check log file.")
                        logging.error(f"[RAW FETCH EXECUTOR] No row found, exception encountered, check log file.")
                except Exception as e:
                    print(f"[RAW FETCH EXECUTOR] Thread worker error encountered processing '{companies_dict.get(company_number, '')}': {str(e)}")
                    logging.exception(f"[RAW FETCH EXECUTOR] Thread worker error encountered processing '{companies_dict.get(company_number, '')}': {str(e)}")

    print(f"\nDone. Records written to {os.path.basename(raw_data_csv_path)}")
    print()

    df_out = pd.read_csv(raw_data_csv_path)
    print(df_out.head(20))    

def fetch():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_PATH = os.path.join(LOG_DIR, 'fetching.log')
    logging.basicConfig(filename=LOG_PATH, 
                        format="%(asctime)s | %(message)s",
                        level=logging.INFO)

    processed_companies: set[str] = set()
    file_exists = os.path.isfile(CSV_SAVE_PATH)

    if file_exists:
        print(f"Existing output file found at: {os.path.basename(CSV_SAVE_PATH)}, reading checkpoints....")
        try:
            with open(CSV_SAVE_PATH, 'a', encoding='utf-8', newline="") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    for csv_row in header:
                        if csv_row and len(csv_row) > 0:
                            processed_companies.add(csv_row[0].strip())
            print(f"Checkpoint loaded, bypassing {len(processed_companies)} completed companies")
        except Exception as e:
            print(f"Failed to parse checkpoint safely: {str(e)}. Starting fresh...")
            file_exists = False

    if not file_exists or os.stat(CSV_SAVE_PATH).st_size == 0:
        with open(CSV_SAVE_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=base_fieldnames)
            writer.writeheader()

    with open(LOG_PATH, 'a', encoding='utf-8', newline='') as log_file:
        df = pd.read_csv(CSV_SAVE_PATH)
        raw_names = [str(n).strip() for n in df['company_name'] if str(n).strip() and str(n).lower() != 'nan']
        todo_names = [name for name in raw_names if name not in processed_companies]

        skipped_count = len(raw_names) - len(todo_names)
        if skipped_count > 0:
            print(f"[FETCH] Bypassing {skipped_count} items (already exist in checkpoint).")

        print(f"[FETCH] Queueing {len(todo_names)} new companies across threadpool...")

        print()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(build_row, company_number): company_number for company_number in company_numbers}
            for future in as_completed(futures):
                company_number = futures[future]
                try:
                    row = future.result()
                    if row:
                        add_record_to_csv(row, CSV_SAVE_PATH)
                        print(f"[EXECUTOR] {companies_dict.get(company_number, company_number)} -> Done.")
                        logging.info(f"[EXECUTOR] {companies_dict.get(company_number, company_number)} -> Done.")
                    else:
                        print(f"[EXECUTOR] No row found, exception encountered, check log file.")
                        logging.error(f"[EXECUTOR] No row found, exception encountered, check log file.")
                except Exception as e:
                    print(f"Thread worker error encountered processing '{companies_dict.get(company_number, '')}': {str(e)}")
                    logging.exception(f"Thread worker error encountered processing '{companies_dict.get(company_number, '')}': {str(e)}")

    print(f"\nDone. Records written to {os.path.basename(CSV_SAVE_PATH)}")
    print()

    df_out = pd.read_csv(CSV_SAVE_PATH)
    print(df_out.head(20))