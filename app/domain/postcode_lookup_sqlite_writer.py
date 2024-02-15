import sqlite3
from typing import Any
from app.domain.postcode_lookup_writer import PostcodeLookupWriter

class PostcodeLookupSqliteWriter(PostcodeLookupWriter):
    def __init__(self, filename: str):
        self.filename = filename

    def initialize_writer(self) -> None:
        self.sqlite_connection = sqlite3.connect(self.filename)
        self.sqlite_cursor = self.sqlite_connection.cursor()
        self.sqlite_cursor.execute(
            """
            CREATE TABLE postcode_lookup(
                postcode TEXT,
                constituency_shortcode TEXT,
                confidence FLOAT
            )
            """
        )
        self.sqlite_cursor.execute("CREATE INDEX idx_postcode_lookup_on_postcode ON postcode_lookup(postcode)")
        self.sqlite_connection.commit()

    def write_row(self, parsed_row: dict[str, Any], confidences: dict[str, float]) -> None:
        for pcon, confidence in confidences.items():
            self.sqlite_cursor.execute(
                """
                INSERT INTO postcode_lookup
                (postcode, constituency_shortcode, confidence)
                VALUES
                (?, ?, ?)
                """,
                (parsed_row['postcode'], pcon, confidence)
            )

    def finalise_writer(self) -> None:
        self.sqlite_connection.commit()
        self.sqlite_cursor.close()
