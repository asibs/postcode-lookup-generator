import glob
from typing import List
import pandas
import psycopg
import re
import subprocess

# Run with: poetry run python -m app.scripts.load_postcodes

CHUNK_SIZE = 10000

def get_file_line_count(filepath: str) -> int:
    cmd_result = subprocess.run(['wc', '-l', filepath], stdout=subprocess.PIPE)
    cmd_output = cmd_result.stdout.decode()
    regex_match = re.search("^[0-9]+", cmd_output)
    line_count = int(regex_match[0])
    return line_count

def print_loading_header() -> None:
    print('=====================> 25% ===================> 50% ===================> 75% ===================> 100%')

def print_loading_dot(chunk_no: int, total_chunks: int) -> None:
    if chunk_no <= 0:
        return

    old_int_percent = (chunk_no-1) * 100 // total_chunks
    new_int_percent = chunk_no * 100 // total_chunks
    for _ in range(new_int_percent - old_int_percent):
        print('.', end='', flush=True)
    
    if chunk_no == total_chunks:
        print('', flush=True)

def find_address_csv_files() -> List[str]:
    return glob.glob('data/2024-01-28/ONS_UPRN_lookup/*.csv')

def create_address_table(connection) -> None:
    with connection.cursor() as cursor:
        # Create the addresses table if not present
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS addresses (
                uprn BIGINT PRIMARY KEY,
                postcode VARCHAR(10),
                northing INTEGER,
                easting INTEGER,
                longitude DECIMAL(18,6),
                latitude DECIMAL(18,6),
                centroid GEOMETRY,
                constituency_code VARCHAR(50)
            )
            """
        )
        connection.commit()

def copy_addresses(file_path: str, connection) -> None:
    with connection.cursor() as cursor:
        with cursor.copy("COPY addresses (uprn, postcode, northing, easting) FROM STDIN") as copy:
            line_count = get_file_line_count(file_path)
            total_chunks = line_count // CHUNK_SIZE

            print_loading_header()

            with pandas.read_csv(file_path, chunksize=CHUNK_SIZE) as reader:
                chunk_no = 0
                for chunk in reader:
                    print_loading_dot(chunk_no, total_chunks)
                    chunk_no += 1
                    for _index, row in chunk.iterrows():
                        copy.write_row((row['UPRN'], row['PCDS'], row['GRIDGB1N'], row['GRIDGB1E']))

        connection.commit()

def set_address_coords(connection) -> None:
    with connection.cursor() as cursor:
        print("Updating centroid of all rows")
        cursor.execute(
            """
            UPDATE addresses
            SET centroid = ST_transform(
                ST_GeomFromText('POINT(' || easting || ' ' || northing || ')', 27700),
                4326
            )
            WHERE centroid IS NULL
            """
        )
        print("Updating lat/lng of all rows")
        cursor.execute(
            """
            UPDATE addresses
            SET latitude = ST_X(centroid), longitude = ST_Y(centroid)
            WHERE latitude IS NULL OR longitude IS NULL
            """
        )
        connection.commit()

def set_constituency(connection) -> None:
    with connection.cursor() as cursor:
        print("Updating constituency of all rows")
        cursor.execute(
            """
            UPDATE addresses a
            SET constituency_code = (
                SELECT p.short_code
                FROM parl_constituencies_2025 p
                WHERE ST_Within(a.centroid, p.geom)
            );
            """
        )
        connection.commit()

def generate_postcode_to_constituency_mappings(connection) -> None:
    with connection.cursor() as cursor:
        print("Creating postcode to constituencies mappings")
        cursor.execute(
            """
            CREATE TABLE postcode_to_constituencies
            AS
            (
                SELECT
                    a.postcode,
                    a.constituency_code,
                    counts.postcode_address_count,
                    COUNT(1) AS postcode_constituency_address_count,
                    ( COUNT(1) * 100.0 / counts.postcode_address_count ) as proportion_of_addresses
                FROM addresses a
                JOIN (
                    SELECT postcode, COUNT(1) AS postcode_address_count
                    FROM addresses
                    GROUP BY 1
                ) counts
                ON a.postcode = counts.postcode
                GROUP BY 1,2,3
                ORDER BY 1,2
            )
            """
        )
        connection.commit()

def load_mysociety_constituencies(connection) -> None:
    with connection.cursor() as cursor:
        print("Loading MySociety postcode to constituencies mappings")
        cursor.execute(
            """
            CREATE TABLE mysociety_postcode_constituencies (
                postcode VARCHAR(10) PRIMARY KEY,
                short_code VARCHAR(50)
            )
            """
        )

        file_path = "data/2024-01-28/mysociety_2025_postcodes_with_constituencies.csv"
        with cursor.copy("COPY mysociety_postcode_constituencies (postcode, short_code) FROM STDIN") as copy:
            csv_file = pandas.read_csv(file_path)
            for _index, line in csv_file.iterrows():
                copy.write_row((line["postcode"], line["short_code"]))

        connection.commit()

def main() -> None:
    files = find_address_csv_files()
    print(f"Found {len(files)} ONS UPRN CSV files")

    with psycopg.connect('user=local password=password host=localhost port=54321 dbname=gis') as conn:
        create_address_table(conn)

        for file_path in sorted(files):
          print(f"Loading data from {file_path}")
          copy_addresses(file_path, conn)

        set_address_coords(conn)
        set_constituency(conn)
        generate_postcode_to_constituency_mappings(conn)
        load_mysociety_constituencies(conn)

if __name__ == '__main__':
    main()


# Once everything is loaded, you can connect to the postgis DB and check for any mismatch with the MySociety data with:
"""
SELECT
    map.postcode,
    map.constituency_code,
    map.proportion_of_addresses,
    map.postcode_address_count,
    mysoc.postcode,
    mysoc.short_code
FROM postcode_to_constituencies map, mysociety_postcode_constituencies mysoc
WHERE map.proportion_of_addresses >= 50.0
AND map.postcode = mysoc.postcode
AND map.constituency_code <> mysoc.short_code
ORDER BY 1;
"""
# TODO: Generate the final postcode -> constituncies map by combining _all_ constituencies from our map AND any from MySoc.
# This should give us every postcode, and the list of possible constituencies - including any postcodes which are in multiple constituencies.
# For those constituencies, we can fallback to the DemoClub postcode lookup (once the election is announced - their API only returns data for boundaries with elections...)