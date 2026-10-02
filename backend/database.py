import duckdb

from backend.config import DB_PATH

def get_connection():

    conn = duckdb.connect(DB_PATH)

    conn.execute("INSTALL spatial")
    conn.execute("LOAD spatial")

    return conn

def initialise_database(csv_path: str):
    conn = get_connection()

    conn.execute("""
                    CREATE OR REPLACE TABLE companies AS
                    SELECT *
                    from read_csv_auto(?) 
                """, [csv_path])

    conn.close()

def find_companies(lon: float, lat: float, radius_km: float):

    radius_metres = radius_km * 1000

    conn = get_connection()

    query = """
                SELECT
                    company_number,
                    company_name,
                    company_type,
                    registered_office_address,
                    lat,
                    lon,

                    ST_Distance_Sphere(
                        ST_Point(lon, lat),
                        ST_Point(?, ?)
                    ) AS distance_metres

                FROM companies

                WHERE
                    lat IS NOT NULL
                    AND
                    lon IS NOT NULL
                    AND
                    ST_Distance_Sphere(
                        ST_Point(lon, lat),
                        ST_Point(?, ?)  
                    ) <= ?

                ORDER BY distance_metres
            """

    result = conn.execute(query, [lon, lat, lon, lat, radius_metres]).fetchdf()

    conn.close()

    return result