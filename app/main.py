import csv
import sqlite3
from datetime import datetime

from app.domain.postcodes import Postcode

# Run with: poetry run python -m app.main

# Read all the constiuency data into a dict, indexed by constituence shortcode
with open('data/mysociety_2025_constituencies.csv', 'r') as constituency_csv:
    reader = csv.DictReader(constituency_csv)
    constituency_data = {
        line['short_code']: line
        for line in reader
    }

# For each postcode, build up the desired data
missing_constituency = 0
invalid_constituency = 0

output_data = []
with open('data/2024-01-28/mysociety_2025_postcodes_with_constituencies.csv', 'r') as postcode_csv:
    reader = csv.DictReader(postcode_csv)
    for line in reader:
        postcode = Postcode(line['postcode'])
        if not postcode.valid():
            print(f"Postcode {line['postcode']} looks invalid.")
        short_code = line['short_code'] or None

        if short_code is None:
            print(f"No constituency found for postcode [{line['postcode']}], shortcode [{short_code}].")
            missing_constituency += 1
            constituency = {}
        elif short_code not in constituency_data:
            print(f"No Constituency found for shortcode [{short_code}] (for postcode [{line['postcode']}]).")
            invalid_constituency += 1
            constituency = {}
        else:
            constituency = constituency_data[short_code]

        output_data.append({
            'postcode_no_space': postcode.unit_postcode(separator=''),
            'postcode_with_space': postcode.unit_postcode(separator=' '),
            'postcode_area': postcode.postcode_area(),
            'postcode_district': postcode.postcode_district(),
            'postcode_sector': postcode.postcode_sector(),
            'postcode_outcode': postcode.outcode(),
            'postcode_incode': postcode.incode(),
            'constituency_shortcode': short_code,
            'constituency_name': constituency.get('name', None),
            'constituency_gss': constituency.get('gss_code', None),
            'constituency_nation': constituency.get('nation', None),
            'constituency_region': constituency.get('region', None),
            'constituency_type': constituency.get('con_type', None),
            'constituency_electorate': constituency.get('electorate', None),
            'constituency_area': constituency.get('area', None),
            'constituency_density': constituency.get('density', None),
            'constituency_center_lat': constituency.get('center_lat', None),
            'constituency_center_lon': constituency.get('center_lon', None),
        })

print(f"Found {missing_constituency} postcodes with no constituency short_code")
print(f"Found {invalid_constituency} postcodes whose constituency short_code was not in the constituency data")

# Write the output
filename = f"postcodes_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
con = sqlite3.connect(f"./output/{filename}.db")

cur = con.cursor()

cur.execute(
    """
    CREATE TABLE postcode_lookup(
        postcode TEXT PRIMARY KEY,
        constituency_shortcode TEXT
    )
    """
)

cur.executemany(
    """
    INSERT INTO postcode_lookup
    (postcode, constituency_shortcode)
    VALUES
    (:postcode_with_space, :constituency_shortcode)
    """,
    output_data
)

con.commit()

cur.close()