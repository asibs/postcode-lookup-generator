from app.domain.postcode_lookup_sqlite_writer import PostcodeLookupSqliteWriter

# Run with: poetry run python -m app.scripts.generate_csv
def main() -> None:
    writer = PostcodeLookupSqliteWriter(filename='data/2024-01-28/output/postcode-lookup.db')
    writer.generate()

if __name__ == '__main__':
    main()
