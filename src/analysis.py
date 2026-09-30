import os
from cleaning import DATA_DIR, CLEAN_CSV_PATH, LOG_DIR
import logging
import pandas as pd
import requests
from dotenv import load_dotenv, find_dotenv
from rate_limiter import RateLimiter
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv(find_dotenv())

GEOAPIFY_KEY = os.getenv("GEOAPIFY_KEY")

ANALYSIS_LOG_PATH = os.path.join(LOG_DIR, 'analysis.log')

ANALYSIS_CSV_PATH = os.path.join(DATA_DIR, 'analysis.csv')

MAX_WORKERS = 6

rate_limiter = RateLimiter(time_frame=1, max_calls=5)

def get_companies_established_by_year(year: int, df: pd.DataFrame):
    df_copy = df.copy()
    companies_by_year_df = df_copy[df_copy['date-of-creation'].astype(str).str.split('-').str[-1].astype(int) >= year]
    logging.info(f"Number of companies established since {year}: {len(companies_by_year_df)}")
    return companies_by_year_df

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
        

def enrich_lat_lon(df: pd.DataFrame, timeout=30):

    df["lat_lon"] = ""

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_index = {}
        for index, row in df.iterrows():
            address = row.get("registered_office_address", "")
            company_name = row.get("company_name", "")
            future = executor.submit(query_lat_lon, address, company_name, timeout)
            future_to_index[future] = index
            print(f"[ENRICH LAT LON] Lat Lon Query | Company Name: {company_name} | Index: {index}")
            logging.info(f"[ENRICH LAT LON] Lat Lon Query | Company Name: {company_name} | Index: {index}")
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                lat_lon, _, _ = future.result()
                print(f"[ENRICH LAT LON] Lat Lon Query Successful | Index: {index}")
                logging.info(f"[ENRICH LAT LON] Lat Lon Query Successful | Index: {index}")
                df.at[index, "lat_lon"] = lat_lon
            except Exception as e:
                print( f"[ENRICH LAT LON] Failed to process row | " f"Index: {index} | " f"Exception: {str(e)}" )
                logging.exception( f"[ENRICH LAT LON] Failed to process row | " f"Index: {index} | " f"Exception: {str(e)}" )
    return df

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
        enriched_lat_lon_df = enrich_lat_lon(df)
        print()
        companies_since_2019_df = get_companies_established_by_year(2019, enriched_lat_lon_df)
        print()
        companies_since_2008_df = get_companies_established_by_year(2008, enriched_lat_lon_df)
        print()
        public_companies_df = get_public_companies(enriched_lat_lon_df)
        print()
        changed_names_df = companies_with_changed_names(enriched_lat_lon_df)
        print()
        changed_names_df.to_csv(ANALYSIS_CSV_PATH)
