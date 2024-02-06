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

populate_db_with_addresses:
	poetry run python -m app.scripts.load_postcodes

clean_install: install_dependencies delete_db start_db populate_db_with_constituency_shapefiles populate_db_with_addresses