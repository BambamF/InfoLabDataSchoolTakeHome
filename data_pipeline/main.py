from fetching import fetch, CSV_SAVE_PATH
from cleaning import clean, CLEAN_CSV_PATH
from analysis import analyse
import os

def main():
    if not os.path.isfile(CSV_SAVE_PATH):
        fetch()
    clean()
    analyse()

if __name__ == "__main__":
    main()