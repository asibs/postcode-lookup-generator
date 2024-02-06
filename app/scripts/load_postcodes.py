from collections import defaultdict
import glob
from typing import List
import pandas
from app.domain.postcodes import Postcode
from app.utils import ceildiv, print_loading_dot, print_loading_header
import psycopg
import re
import subprocess
import time

# Run with: poetry run python -m app.scripts.load_postcodes

CHUNK_SIZE = 10_000

def get_file_line_count(filepath: str) -> int:
    cmd_result = subprocess.run(['wc', '-l', filepath], stdout=subprocess.PIPE)
    cmd_output = cmd_result.stdout.decode()
    regex_match = re.search("^[0-9]+", cmd_output)
    line_count = int(regex_match[0])
    return line_count

##### UPRN helper methods #####

def find_uprn_csv_files() -> List[str]:
    return glob.glob('data/2024-01-28/input/ONS_UPRN_lookup/*.csv')

def create_uprn_address_table(connection) -> None:
    with connection.cursor() as cursor:
        # Create the addresses table if not present
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS uprn_addresses (
                uprn BIGINT PRIMARY KEY,
                postcode VARCHAR(10),
                northing INTEGER,
                easting INTEGER,
                longitude DECIMAL(18,6),
                latitude DECIMAL(18,6),
                centroid GEOMETRY
            )
            """
        )
        connection.commit()

def copy_addresses_from_uprn_file(file_path: str, connection) -> None:
    invalid_postcodes = defaultdict(int)

    with connection.cursor() as cursor:
        with cursor.copy("COPY uprn_addresses (uprn, postcode, northing, easting) FROM STDIN") as copy:
            line_count = get_file_line_count(file_path)
            total_chunks = ceildiv(line_count, CHUNK_SIZE)

            print_loading_header()

            # keep_default_na=False prevents pandas from translating empty strings to 'nan'
            with pandas.read_csv(file_path, chunksize=CHUNK_SIZE, dtype={'PCDS':str}, keep_default_na=False) as reader:
                chunk_no = 0
                for chunk in reader:
                    print_loading_dot(chunk_no, total_chunks)
                    chunk_no += 1
                    for _index, row in chunk.iterrows():
                        postcode = Postcode(row['PCDS'])
                        if not postcode.valid():
                            invalid_postcodes[row['PCDS']] += 1
                        copy.write_row((row['UPRN'], postcode.unit_postcode(), row['GRIDGB1N'], row['GRIDGB1E']))

        connection.commit()
    
    for k,v in invalid_postcodes.items():
        print (f"{time.ctime()} - Found {v} addresses with invalid postcode: [{k}]")

def set_uprn_address_coords(connection) -> None:
    # Method inspiried by / copied from:
    # https://alexlittledice.wordpress.com/2016/05/01/geocoding-with-postgis/
    # https://8kb.co.uk/blog/2014/03/16/uk-geographic-postcode-data-latitude-longitude-royal-mail-paf-and-ordnance-survey-data/
    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Updating centroid of all addresses")
        cursor.execute(
            """
            UPDATE uprn_addresses
            SET centroid = ST_transform(
                ST_GeomFromText('POINT(' || easting || ' ' || northing || ')', 27700),
                4326
            )
            WHERE centroid IS NULL
            """
        )
        print(f"{time.ctime()} - Updating lat/lng of all addresses")
        cursor.execute(
            """
            UPDATE uprn_addresses
            SET latitude = ST_X(centroid), longitude = ST_Y(centroid)
            WHERE latitude IS NULL OR longitude IS NULL
            """
        )
        connection.commit()

def create_uprn_address_constituency_map(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(1) FROM uprn_addresses")
        count_result = cursor.fetchone()
        count = count_result[0]
        print(f"{time.ctime()} - Creating address to constituency mapping for all {count} addresses - this can take a couple of hours!")

        # Note, batching this by using a sub-query on uprn_addresses and a LIMIT/OFFSET would allow us to output
        # progress on the command line. This works for the first few batches, but starts to slow down exponentially.
        # It's significantly quicker to run it as a single statement.
        cursor.execute(
            """
            CREATE TABLE uprn_address_to_constituency AS
                SELECT a.uprn, pcon.short_code AS constituency_code
                FROM uprn_addresses a
                LEFT JOIN parl_constituencies_2025 pcon
                ON ST_Within(a.centroid, pcon.geom)
            """
        )
        connection.commit()

def generate_uprn_postcode_to_constituency_mappings(connection) -> None:
    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Creating UPRN postcode to constituencies mappings")
        cursor.execute(
            """
            CREATE TABLE uprn_postcode_to_constituency AS (
                SELECT
                    a.postcode,
                    map.constituency_code,
                    counts.postcode_address_count,
                    COUNT(1) AS postcode_constituency_address_count,
                    ( COUNT(1) * 100.0 / counts.postcode_address_count ) as proportion_of_addresses
                FROM uprn_addresses a
                JOIN uprn_address_to_constituency map
                ON a.uprn = map.uprn
                JOIN (
                    SELECT postcode, COUNT(1) AS postcode_address_count
                    FROM uprn_addresses
                    GROUP BY 1
                ) counts
                ON a.postcode = counts.postcode
                GROUP BY 1,2,3
                ORDER BY 1,2
            )
            """
        )
        connection.commit()

##### ONSPD helper methods #####

def find_onspd_csv_files() -> List[str]:
    return glob.glob('data/2024-01-28/input/ONS_postcode_directory/*.csv')

def create_onspd_postcodes_table(connection) -> None:
    with connection.cursor() as cursor:
        # Create the postcodes table if not present
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS onspd_postcodes (
                postcode VARCHAR(10) PRIMARY KEY,
                longitude DECIMAL(18,6),
                latitude DECIMAL(18,6),
                centroid GEOMETRY
            )
            """
        )
        connection.commit()

def copy_postcodes_from_onspd_file(file_path: str, connection) -> None:
    terminated_postcodes = []
    invalid_postcodes = []

    with connection.cursor() as cursor:
        with cursor.copy("COPY onspd_postcodes (postcode, latitude, longitude) FROM STDIN") as copy:
            line_count = get_file_line_count(file_path)
            total_chunks = ceildiv(line_count, CHUNK_SIZE)

            print_loading_header()

            # keep_default_na=False prevents pandas from translating empty strings to 'nan'
            with pandas.read_csv(file_path, chunksize=CHUNK_SIZE, dtype={'pcds':str, 'doterm':str}, keep_default_na=False) as reader:
                chunk_no = 0
                for chunk in reader:
                    print_loading_dot(chunk_no, total_chunks)
                    chunk_no += 1
                    for _index, row in chunk.iterrows():
                        postcode = Postcode(row['pcds'])
                        if row['doterm'] is not None and row['doterm'] != '':
                            terminated_postcodes.append(row['pcds'])
                        elif not postcode.valid():
                            invalid_postcodes.append(row['pcds'])
                        else:
                            copy.write_row((postcode.unit_postcode(), row['lat'], row['long']))

        connection.commit()
    
    print(f"{time.ctime()} - Skipped {len(terminated_postcodes)} terminated postcodes.")
    for p in invalid_postcodes:
        print(f"{time.ctime()} - Skipped invalid postcode: [{p}]")

def set_onspd_postcode_coords(connection) -> None:
    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Updating centroid of all postcodes")
        cursor.execute(
            """
            UPDATE onspd_postcodes
            SET centroid = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            WHERE centroid IS NULL
            """
        )
        connection.commit()

def create_onspd_postcode_constituency_map(connection) -> None:
    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Creating postcodes to constituency mapping for all postcodes")
        cursor.execute(
            """
            CREATE TABLE onspd_postcode_to_constituency AS (
                SELECT pc.postcode, pcon.short_code AS constituency_code
                FROM onspd_postcodes pc, parl_constituencies_2025 pcon
                WHERE ST_Within(pc.centroid, pcon.geom)
            )
            """
        )
        connection.commit()

##### MySociety helper methods #####

def load_mysociety_constituencies(connection) -> None:
    invalid_postcodes = []

    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Loading MySociety postcode to constituencies mappings")
        cursor.execute(
            """
            CREATE TABLE mysociety_postcode_to_constituency (
                postcode VARCHAR(10) PRIMARY KEY,
                constituency_code VARCHAR(50)
            )
            """
        )

        file_path = "data/2024-01-28/input/mysociety_2025_postcodes_with_constituencies.csv"
        with cursor.copy("COPY mysociety_postcode_to_constituency (postcode, constituency_code) FROM STDIN") as copy:
            # keep_default_na=False prevents pandas from translating empty strings to 'nan'
            csv_file = pandas.read_csv(file_path, dtype={'postcode':str, 'short_code':str}, keep_default_na=False)
            for _index, line in csv_file.iterrows():
                postcode = Postcode(line['postcode'])
                if not postcode.valid():
                    invalid_postcodes.append(line['postcode'])
                copy.write_row((postcode.unit_postcode(), line["short_code"] or None))

        connection.commit()
    
    for p in invalid_postcodes:
        print(f"{time.ctime()} - Found invalid postcode: [{p}]")

##### Combining it all #####

def create_combo_constituency_map(connection) -> None:
    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Creating postcode to constituency mapping combining all sources")
        cursor.execute(
            """
            CREATE TABLE combined_postcode_to_constituency AS (
                SELECT
                  postcode,
                  COALESCE(constituency_code, 'UNKNOWN') AS constituency_code,
                  'UPRN' AS source,
                  proportion_of_addresses::TEXT || ' percent of addresses in postcode' AS notes
                FROM uprn_postcode_to_constituency

                UNION

                SELECT
                  postcode,
                  COALESCE(constituency_code, 'UNKNOWN') AS constituency_code,
                  'ONSPD' AS source,
                  '' AS notes
                FROM onspd_postcode_to_constituency

                UNION

                SELECT
                  postcode,
                  COALESCE(constituency_code, 'UNKNOWN') AS constituency_code,
                  'MySociety' AS source,
                  '' AS notes
                FROM mysociety_postcode_to_constituency
            )
            """
        )
        connection.commit()

def create_multi_column_constituency_map(connection) -> None:
    with connection.cursor() as cursor:
        print(f"{time.ctime()} - Creating multi-column postcode to constituency mapping combining all sources")
        cursor.execute(
            """
            CREATE TABLE combined_postcode_to_constituency_multicol AS (
                SELECT
                    COALESCE(uprn_and_onspd.postcode, mysoc.postcode) AS postcode,
                    uprn_pcon_1, uprn_pcon_2, uprn_pcon_3, uprn_pcon_4, uprn_pcon_5,
                    onspd_pcon, mysociety_pcon
                FROM (
                    SELECT
                        COALESCE(uprn.postcode, onspd.postcode) AS postcode,
                        uprn_pcon_1, uprn_pcon_2, uprn_pcon_3, uprn_pcon_4, uprn_pcon_5,
                        onspd_pcon
                    FROM (
                        SELECT                                                                  
                            postcode,
                            constituencies[1] AS uprn_pcon_1,
                            constituencies[2] AS uprn_pcon_2,
                            constituencies[3] AS uprn_pcon_3,
                            constituencies[4] AS uprn_pcon_4,
                            constituencies[5] AS uprn_pcon_5
                        FROM (
                            SELECT
                                postcode,
                                array_agg(COALESCE(constituency_code, 'UNKNOWN') ORDER BY proportion_of_addresses DESC) AS constituencies
                            FROM uprn_postcode_to_constituency
                            GROUP BY postcode
                        )
                    ) uprn
                    FULL OUTER JOIN (
                        SELECT postcode, COALESCE(constituency_code, 'UNKNOWN') AS onspd_pcon FROM onspd_postcode_to_constituency
                    ) onspd
                    ON uprn.postcode = onspd.postcode
                ) uprn_and_onspd
                FULL OUTER JOIN (
                    SELECT postcode, COALESCE(constituency_code, 'UNKNOWN') AS mysociety_pcon FROM mysociety_postcode_to_constituency
                ) mysoc
                ON mysoc.postcode = uprn_and_onspd.postcode
            )
            """
        )
        connection.commit()

##### MAIN #####

def main() -> None:
    with psycopg.connect('user=local password=password host=localhost port=54321 dbname=gis') as conn:
        # # UPRN Processing
        # uprn_files = find_uprn_csv_files()
        # print(f"{time.ctime()} - Found {len(uprn_files)} ONS UPRN CSV files")

        # create_uprn_address_table(conn)

        # for file_path in sorted(uprn_files):
        #   print(f"{time.ctime()} - Loading data from {file_path}")
        #   copy_addresses_from_uprn_file(file_path, conn)

        # set_uprn_address_coords(conn)
        # create_uprn_address_constituency_map(conn)
        # generate_uprn_postcode_to_constituency_mappings(conn)

        # # ONSPD processing
        # onspd_files = find_onspd_csv_files()
        # print(f"{time.ctime()} - Found {len(onspd_files)} ONSPD CSV files")

        # create_onspd_postcodes_table(conn)

        # for file_path in sorted(onspd_files):
        #   print(f"{time.ctime()} - Loading data from {file_path}")
        #   copy_postcodes_from_onspd_file(file_path, conn)

        # set_onspd_postcode_coords(conn)
        # create_onspd_postcode_constituency_map(conn)

        # # MySociety processing
        # load_mysociety_constituencies(conn)

        # Combine the data
        create_combo_constituency_map(conn)
        create_multi_column_constituency_map(conn)


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
    mysoc.constituency_code
FROM postcode_to_constituency map, mysociety_postcode_constituency mysoc
WHERE map.proportion_of_addresses >= 50.0
AND map.postcode = mysoc.postcode
AND map.constituency_code <> mysoc.constituency_code
ORDER BY 1;
"""
# TODO: Generate the final postcode -> constituncies map by combining _all_ constituencies from our map AND any from MySoc.
# This should give us every postcode, and the list of possible constituencies - including any postcodes which are in multiple constituencies.
# For those constituencies, we can fallback to the DemoClub postcode lookup (once the election is announced - their API only returns data for boundaries with elections...)