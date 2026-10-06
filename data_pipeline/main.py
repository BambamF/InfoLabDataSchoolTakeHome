from fetching import fetch, CSV_SAVE_PATH, raw_data_fetch, DATA_DIR, LOG_DIR
from cleaning import clean, CLEAN_CSV_PATH
from analysis import analyse
import os

def main():
    """
    if not os.path.isfile(CSV_SAVE_PATH):
        fetch()
    clean()
    analyse()    
    """
    csv_path = os.path.join(DATA_DIR, 'raw_data.csv')
    log_path = os.path.join(LOG_DIR, 'raw_data.log')
    raw_data_fetch(csv_path, log_path)


if __name__ == "__main__":
    main()