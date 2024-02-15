from app.domain.postcode_lookup_csv_writer import PostcodeLookupCsvWriter

# Run with: poetry run python -m app.scripts.generate_csv
def main() -> None:
    writer = PostcodeLookupCsvWriter(
        filename='data/2024-01-28/output/postcode-lookup.csv',
        write_confidences=False
    )
    writer.generate()

if __name__ == '__main__':
    main()
