from database import initialise_database
import os
from data_pipeline.fetching import DATA_DIR

CSV_PATH = os.path.join(DATA_DIR,"analysis.csv")

if __name__ == "__main__":
    initialise_database(CSV_PATH)

    print("DUCKDB database initialised successfully")