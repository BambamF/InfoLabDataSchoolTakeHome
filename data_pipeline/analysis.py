import os
from cleaning import DATA_DIR, CLEAN_CSV_PATH, LOG_DIR
import logging
import pandas as pd
import requests
from dotenv import load_dotenv, find_dotenv
from rate_limiter import RateLimiter
import time

load_dotenv(find_dotenv())

GEOAPIFY_KEY = os.getenv("GEOAPIFY_KEY")

ANALYSIS_LOG_PATH = os.path.join(LOG_DIR, 'analysis.log')

ANALYSIS_CSV_PATH = os.path.join(DATA_DIR, 'analysis.csv')

MAX_WORKERS = 6

BATCH_SIZE = 1000
POLL_INTERVAL = 60
MAX_POLL_ATTEMPTS = 100

rate_limiter = RateLimiter(time_frame=1, max_calls=5)

def get_companies_established_by_year(year: int, df: pd.DataFrame):
    df_copy = df.copy()
    companies_by_year_df = df_copy[df_copy['date_of_creation'].astype(str).str.split('-').str[0].astype(int) >= year]
    logging.info(f"Number of companies established since {year}: {len(companies_by_year_df)}")
    print(f"Number of companies established since {year}: {len(companies_by_year_df)}")
    return companies_by_year_df

def get_companies_established_in_year(year: int, df: pd.DataFrame):
    df_copy = df.copy()
    companies_in_year_df = df_copy[df_copy['date_of_creation'].astype(str).str.split('-').str[0].astype(int) == year]
    logging.info(f"Number of companies established in {year}: {len(companies_in_year_df)}")
    print(f"Number of companies established in {year}: {len(companies_in_year_df)}")
    return companies_in_year_df

def query_lat_lon(address: str, company_name: str, timeout: int):
    url = 'https://api.geoapify.com/v1/geocode/search'
    params = {'text': address,
              'apiKey': GEOAPIFY_KEY}
    retry = 1.0
    for i in range(5):
        rate_limiter.acquire()
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            features = data.get("features", [])
            if not features:
                logging.warning(f"[QUERY LAT LON] No results | Company Name: {company_name} | Address: {address} | Turn: {i}")
                return "", None, None

            lat = features[0].get('properties', '').get('lat', '')
            lon = features[0].get('properties', '').get('lon', '')

            if lat is None or lon is None:
                logging.warning(f"[QUERY LAT LON] Missing Coordinates | Company Name: {company_name} | Address: {address} | Turn: {i}")

                return "", lat, lon

            lat_lon = f"{lat}, {lon}"
            logging.info(f"[QUERY LAT LON] Query successful | Company Name: {company_name} | URL: {url} | Turn: {i}  Address: {address} | Lat, Lon: {lat_lon if lat_lon else 'empty'} | Lat: {lat} | Lon: {lon}")

        except Exception as e:

            print(f"QUERY LAT LON] Exception Encountered | Company Name: {company_name} | Retry: {retry} | Turn: {i} | URL: {url} | Address: {address} | Exception: {str(e)}")
            logging.exception(f"QUERY LAT LON] Exception Encountered | Company Name: {company_name} | Retry: {retry} | Turn: {i} | URL: {url} | Address: {address} | Exception: {str(e)}")
            time.sleep(retry)
            retry *= 2
            continue
    logging.error(f"[QUERY LAT LON] All retries failed | Company Name: {company_name} | Address: {address}")
    return "", None, None
        
def submit_geocoding_batch(addresses: list[str], timeout: int = 30):
    url = "https://api.geoapify.com/v1/batch/geocode/search"
    params = {
        "apiKey": GEOAPIFY_KEY
    }

    response = requests.post(
        url,
        params=params,
        json=addresses,
        timeout=timeout
    )

    response.raise_for_status()

    data = response.json()

    job_id = data["id"]
    results_url = data["url"]

    logging.info(f"[SUBMIT GEOCODING BATCH] Job ID: {job_id} | Number of Addresses: {len(addresses)}")
    return job_id, results_url

def get_batch_results(results_url: str, timeout: int = 30):
    for i in range(MAX_POLL_ATTEMPTS):
        response = requests.get(results_url, timeout=timeout)
        if response.status_code == 200:
            logging.info(f"[GET BATCH RESULTS] Batch Complete | Attempt: {i}")
            return response.json()
        if response.status_code == 202:
            logging.info(f"[GET BATCH RESULTS] Batch Pending | Attempt: {i} | Retry in {POLL_INTERVAL} seconds...")
            time.sleep(POLL_INTERVAL)
            continue
        response.raise_for_status()
    raise TimeoutError(f"[GET BATCH RESULTS] Batch job did not finish after {MAX_POLL_ATTEMPTS} retries...")

def enrich_lat_lon(df: pd.DataFrame):
    df_copy = df.copy()

    df_copy["lat"] = None 
    df_copy["lon"] = None 
    df_copy["lat_lon"] = ""

    address_df = df_copy[["registered_office_address"]].copy()

    address_df = address_df.dropna(subset=["registered_office_address"])

    address_df["registered_office_address"] = address_df["registered_office_address"].astype(str).str.strip()

    address_df = address_df[address_df["registered_office_address"] != ""]

    unique_addresses_df = address_df["registered_office_address"].drop_duplicates().tolist()

    logging.info(f"[ENRICH LAT LON] Total dataframe rows: {len(df_copy)}")
    logging.info(f"[ENRICH LAT LON] Unique addresses: {len(unique_addresses_df)}")
    print(f"[ENRICH LAT LON] Total dataframe rows: {len(df_copy)}")
    print(f"[ENRICH LAT LON] Unique addresses: {len(unique_addresses_df)}")

    addresses_lat_lon_map = {}

    for i in range(0, len(unique_addresses_df), BATCH_SIZE):
        batch = unique_addresses_df[i:i+BATCH_SIZE]
        batch_number = (i // BATCH_SIZE) + 1
        logging.info(f"[ENRICH LAT LON] Submitting batch {i} | Number of Addresses: {len(batch)}")
        print(f"[ENRICH LAT LON] Submitting batch {i} | Number of Addresses: {len(batch)}")

        job_id, results_url = submit_geocoding_batch(batch)

        logging.info(f"[ENRICH LAT LON] Job Submitted | Batch: {batch_number} | Job ID: {job_id}")
        print(f"[ENRICH LAT LON] Job Submitted | Batch: {batch_number} | Job ID: {job_id}")

        results = get_batch_results(results_url)

        logging.info(f"[ENRICH LAT LON] Processing results | Batch: {batch_number}")
        print(f"[ENRICH LAT LON] Processing results | Batch: {batch_number}")
        print(f"[ENRICH LAT LON] Batch {batch_number}: {len(results)} results received")

        for result in results:
            address = result.get("query", {}).get("text", "")

            lat = result.get("lat")
            lon = result.get("lon")

            if address and lat is not None and lon is not None:
                addresses_lat_lon_map[address] = (lat, lon)
    
    for index, row in df_copy.iterrows():

        address = row.get("registered_office_address", "")

        if not isinstance(address, str):
            continue

        address = address.strip()

        coordinates = addresses_lat_lon_map.get(address)

        if coordinates is None:
            continue

        lat, lon = coordinates

        df_copy.at[index, "lat"] = lat 
        df_copy.at[index, "lon"] = lon 
        df_copy.at[index, "lat_lon"] = f"{lat}, {lon}"

    logging.info(f"[ENRICH LAT LON] Geocoding Completed Successfully | {len(addresses_lat_lon_map)} unique addresses")
    print(f"[ENRICH LAT LON] Successfully geocoded: {len(addresses_lat_lon_map)} {len(unique_addresses_df)} addresses")

    

    return df_copy

def get_public_companies(df: pd.DataFrame):
    df_copy = df.copy()
    public_companies_df = df_copy[(df_copy['company_type'] == 'plc') | (df_copy['company_type'] == 'public_limited_company')]
    print(f"Number of Public Companies: {len(public_companies_df)}")
    return public_companies_df

def companies_with_changed_names(df: pd.DataFrame):
    df_copy = df.copy()
    changed_names_df = df_copy[df_copy['previous_company_names'].notna()]
    print(f"Number of Companies That Have Changed Names: {len(changed_names_df)}")
    return changed_names_df

def analyse():
    logging.basicConfig(filename=ANALYSIS_LOG_PATH,
                        level=logging.INFO,
                        format="%(asctime)s | %(message)s")
    with open(ANALYSIS_LOG_PATH, 'a', encoding='utf-8', newline="") as log_file:
        df = pd.read_csv(CLEAN_CSV_PATH)
        print()
        if not os.path.isfile(ANALYSIS_CSV_PATH):
            enriched_lat_lon_df = enrich_lat_lon(df)
            enriched_lat_lon_df.to_csv(ANALYSIS_CSV_PATH, index=False)
        enriched_lat_lon_df = pd.read_csv(ANALYSIS_CSV_PATH)
        print()
        companies_since_2019_df = get_companies_established_by_year(2019, enriched_lat_lon_df)
        print()
        companies_since_2008_df = get_companies_established_by_year(2008, enriched_lat_lon_df)
        print()
        companies_in_2008_df = get_companies_established_in_year(2008, enriched_lat_lon_df)
        print()
        public_companies_df = get_public_companies(enriched_lat_lon_df)
        print()
        changed_names_df = companies_with_changed_names(enriched_lat_lon_df)
        print()
        print(changed_names_df["date_of_creation"].head(10))