import os
from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_KEY = os.getenv("GEOAPIFY_KEY")

DB_PATH = os.getenv("DUCKDB_PATH", "data/companies.duckdb")

if not GEOAPIFY_KEY:
    raise RuntimeError("GEOAPIFY_KEY is not configured")

