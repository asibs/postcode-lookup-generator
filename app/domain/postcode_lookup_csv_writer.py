import csv
from typing import Any
from app.domain.postcode_lookup_writer import PostcodeLookupWriter

class PostcodeLookupCsvWriter(PostcodeLookupWriter):
    def __init__(self, filename: str, write_confidences: bool):
        self.filename = filename
        self.write_confidences = write_confidences

    def initialize_writer(self) -> None:
        self.file = open(self.filename, 'w')
        self.writer = csv.writer(self.file)

        csv_header = ['postcode']
        for i in range(6):
            csv_header.append(f"pcon_{i+1}")
            if self.write_confidences:
                csv_header.append(f"confidence_{i+1}")

        self.writer.writerow(csv_header)

    def write_row(self, parsed_row: dict[str, Any], confidences: dict[str, float]) -> None:
        csv_row = [parsed_row['postcode']]
        for pcon, confidence in sorted(confidences.items(), key=lambda x: (-x[1])):
            csv_row.append(pcon)
            if self.write_confidences:
                csv_row.append(confidence)
    
        self.writer.writerow(csv_row)

    def finalise_writer(self) -> None:
        self.file.close()
