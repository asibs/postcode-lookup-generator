.PHONY:

install_dependencies:
	poetry install

start_db:
	docker compose up -d --wait

stop_db:
	docker compose down

delete_db:
	docker compose down -v

populate_db_with_constituency_shapefiles:
	ogr2ogr -f PostgreSQL \
		"PG:user=local password=password dbname=gis host=localhost port=54321" \
		data/2024-01-28/input/mysociety_2025_constituencies_boundaries.gpkg

populate_db_with_postcode_data:
	poetry run python -m app.scripts.load_postcodes

generate_csv_postcode_lookup:
  poetry run python -m app.scripts.generate_csv

generate_sqlite_postcode_lookup:
  poetry run python -m app.scripts.generate_sqlite

clean_install: install_dependencies delete_db start_db populate_db_with_constituency_shapefiles populate_db_with_postcode_data