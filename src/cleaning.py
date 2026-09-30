import os
import pandas as pd
from fetching import DATA_DIR, LOG_DIR, CSV_SAVE_PATH
import logging



CLEAN_CSV_PATH = os.path.join(DATA_DIR, 'clean_data.csv')

INIT_CSV_PATH = CSV_SAVE_PATH

CLEAN_LOG_PATH = os.path.join(LOG_DIR, 'cleaning.log')

def print_df_details(df: pd.DataFrame):
    rows, columns = df.shape
    print()
    print(f"Number of Rows in Dataframe: {rows}\n")
    print(f"Number of columns in Dataframe: {columns}\n")
    print(f"Columns: {df.columns}\n")
    print(f"Dataframe types: {df.dtypes.to_string()}\n")

def print_missing_values(df: pd.DataFrame):
    missing_values = df.isnull().sum()
    logging.info(f"[PRINT MISSING VALUES] Missing values by column: {missing_values}")
    most_affected = missing_values.idxmax()
    logging.info(f"[PRINT MISSING VALUES] Most affected column: {missing_values.idxmax()}")
    print(f"Missing values:\n{missing_values.sort_values(ascending=False).head(3)}\n")
    print(f"Most affected columns:\n{most_affected}\n")
    logging.info(f"[PRINT MISSING VALUES] Number of missing values: {missing_values.sum()}")
    return missing_values.sum()

def remove_duplicates(df: pd.DataFrame):
    new_df = df.copy()
    abs_deduped_df = new_df.drop_duplicates()
    print(f"Original dataset size: {len(new_df)}")
    logging.info(f"Original dataset size: {len(new_df)}")
    print(f"Number of entries after absolute Dedupe: {len(abs_deduped_df)}\n")
    logging.info(f"Number of entries after absolute Dedupe: {len(abs_deduped_df)}\n")
    name_deduped_df = new_df.drop_duplicates(subset=["company_name"])
    print(f"Number of entries after Dedupe on company name: {len(name_deduped_df)}")
    logging.info(f"Number of entries after Dedupe on company name: {len(name_deduped_df)}")
    return abs_deduped_df, name_deduped_df

def clean_company_details(df: pd.DataFrame):
    df_copy = df.copy()
    df_copy["company_name"] = df_copy["company_name"].str.strip()
    df_copy["company_number"] = df_copy["company_number"].str.strip() # not converting to numeric as company number can contain string characters
    return df_copy

def clean_null_columns(df: pd.DataFrame):
    df_copy = df.copy()
    cleaned_columns = df_copy.dropna(axis=1, how='all', inplace=True)
    return df_copy

def clean():
    logging.basicConfig(filename=CLEAN_LOG_PATH,
                        level=logging.INFO,
                        format="%(asctime)s | %(message)s")

    with open(CLEAN_LOG_PATH, 'a', encoding='utf-8', newline="") as log_file:
            init_df = pd.read_csv(INIT_CSV_PATH)
            print_df_details(init_df)
            print()
            print(f"Total Missing Values: {print_missing_values(init_df)}")
            print()
            abs_deduped_df, name_deduped_df = remove_duplicates(init_df)
            print()
            clean_details_df = clean_company_details(abs_deduped_df)
            print()
            clean_columns_df = clean_null_columns(clean_details_df)
            print(f"Number of columns after Nan column removal: {clean_columns_df.shape[1]}")
            print()
            print(clean_columns_df.head(20))
            clean_columns_df.to_csv(CLEAN_CSV_PATH)
