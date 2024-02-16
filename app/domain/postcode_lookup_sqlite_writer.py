import re
import sqlite3
from app.domain.postcodes import Postcode
import psycopg
from typing import Any, Dict, List
from app.domain.postcode_lookup_writer import PostcodeLookupWriter

class PostcodeLookupSqliteWriter(PostcodeLookupWriter):
    def __init__(self, filename: str):
        self.filename = filename

    def initialize_writer(self) -> None:
        self.sqlite_connection = sqlite3.connect(self.filename)
        self.sqlite_cursor = self.sqlite_connection.cursor()

        # Create pcon lookup table
        self.sqlite_cursor.execute(
            """
            CREATE TABLE pcon(
                id INTEGER PRIMARY KEY,
                short_code TEXT,
                name TEXT,
                slug TEXT
            )
            """
        )
        for pcon in self._get_pcon_data():
            self.sqlite_cursor.execute(
                """
                INSERT INTO pcon (short_code, name, slug)
                VALUES (?, ?, ?)
                """,
                (pcon['short_code'], pcon['name'], pcon['slug'])
            )


        self.sqlite_cursor.execute(
            """
            CREATE TABLE postcode_lookup(
                postcode TEXT,
                pcon_id TEXT,
                confidence FLOAT
            )
            """
        )
        self.sqlite_cursor.execute("CREATE INDEX idx_postcode_lookup_on_postcode ON postcode_lookup(postcode)")
        self.sqlite_connection.commit()

    def write_row(self, parsed_row: dict[str, Any], confidences: dict[str, float]) -> None:
        for pcon, confidence in confidences.items():
            normalised_postcode = Postcode(parsed_row['postcode']).unit_postcode(separator='')
            self.sqlite_cursor.execute(
                """
                INSERT INTO postcode_lookup
                (postcode, pcon_id, confidence)
                VALUES
                (?, (SELECT id FROM pcon WHERE short_code = ?), ?)
                """,
                (normalised_postcode, pcon, confidence)
            )

    def finalise_writer(self) -> None:
        self.sqlite_connection.commit()
        self.sqlite_cursor.close()

    def _get_pcon_data(self) -> List[Dict]:
        with psycopg.connect('user=local password=password host=localhost port=54321 dbname=gis') as conn:
          with conn.cursor() as cursor:
              cursor.execute("SELECT short_code, name FROM parl_constituencies_2025")
              return [
                  {'short_code': row[0], 'name': row[1], 'slug': self._pcon_name_to_slug(row[1])}
                  for row in cursor.fetchall()
              ]
    
    def _pcon_name_to_slug(self, name: str) -> str:
        # Replace one or more non-alphabetical chars (including whitespace) with a single dash
        return re.sub('[^a-z]+', '-', name.lower())
