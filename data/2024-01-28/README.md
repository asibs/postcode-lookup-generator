# 2024-01-28 version

To get all the data:

- Ensure you are in the `data/2024-01-28/` directory
- `wget -O input/mysociety_2025_constituencies.csv https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.csv`
- `wget -O input/mysociety_2025_constituencies_boundaries.gpkg https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.gpkg`
- Manually download the [UPRN data from here](https://geoportal.statistics.gov.uk/datasets/9e5789e21a374f4c91dc4fac976003dc/about), unzip, and copy the data files (`NSUL_JAN_2024_*.csv`) into the `input/ONS_UPRN_lookup` folder (this could probably be automated with a wget & gunzip combo)
- Manually download the [ONSPD data from here](https://geoportal.statistics.gov.uk/datasets/3700342d3d184b0d92eae99a78d9c7a3/about), unzip, and copy the data file (`ONSPD_NOV_2023_UK.csv`) into the `input/ONS_postcode_directory` folder (this could probably be automated with a wget & gunzip combo)

If you don't have the `wget` command line utility (eg. Windows) you can manually download the files and rename them appropriately.

## mySociety Constituency Data, including boundaries (V0.1.4)

### Files

- `mysociety_2025_constituencies.csv`
- `mysociety_2025_constituencies_boundaries.gpkg`

### Source

https://pages.mysociety.org/2025-constituencies/datasets/parliament_con_2025/0_1_4

### Notes

This data relates to the "new" boundaries for UK Parliamentary Constituencies - which come into force for general elections from 2024/2025.

### Licence

Creative Commons Attribution 4.0 International License

https://pages.mysociety.org/2025-constituencies/datasets/parliament_con_2025/0_1_4

## mySociety Postcode Data (V0.1.2)

### Files

- `mysociety_2025_postcodes_with_constituencies.csv`

### Source

https://pages.mysociety.org/2025-constituencies/datasets/uk_parliament_2025_postcode_lookup/0_1_2

### Notes

This maps UK postcodes to their "new" UK Parliamentary Constituency (the 2024/2025 constituencies).

### Licence

Creative Commons Attribution 4.0 International License

https://pages.mysociety.org/2025-constituencies/datasets/uk_parliament_2025_postcode_lookup/0_1_2

## National Statistics UPRN Lookup (January 2024)

### Files

- `ONS_UPRN_lookup/NSUL_JAN_2024_*.csv`

### Source

https://geoportal.statistics.gov.uk/datasets/9e5789e21a374f4c91dc4fac976003dc/about

### Notes

This dataset maps every Unique Property Reference Number (UPRN) - which represents an address in the UK - to a variety
of geographies, including Westminster parliamentary constituency. Unfortunately, this dataset does not (yet) include
the "new" UK Parliamentary Constituency boundaries - it uses the "current" boundaries which will not be used in the
next general election in 2024 or 2025. It does include National Grid Reference co-ordinates for each address, which can
be converted to latitude/longitude to work out which new constituency the address falls within.

### License

- Contains OS data © Crown copyright and database right 2024
- Contains Royal Mail data © Royal Mail copyright and Database right 2024
- Contains GeoPlace data © Local Government Information House Limited copyright and database right 2024
- Source: Office for National Statistics licensed under the Open Government Licence v.3.0

https://www.ons.gov.uk/methodology/geography/licences

## National Statistics Postcode Directory (November 2023)

### Files

- `ONS_postcode_directory/ONSPD_NOV_2023_*.csv`

### Source

https://geoportal.statistics.gov.uk/datasets/3700342d3d184b0d92eae99a78d9c7a3/about

### Notes

This dataset maps postcodes - including terminated postcodes - to a variety of geographies, including Westminster
parliamentary consituency. Similar to the UPRN dataset, this does not (yet) include the "new" UK Parliamentary
Constituency boundaries - it uses the "current" boundaries which will not be used in the next general election in
2024 or 2025. The ONSPD does include National Grid Reference co-ordaintes, and latitude/longitude, which we can use to
work out which new constituency the postcode centroid falls within.

### License

- Contains OS data © Crown copyright and database right 2024
- Contains Royal Mail data © Royal Mail copyright and Database right 2024
- Contains GeoPlace data © Local Government Information House Limited copyright and database right 2024
- Source: Office for National Statistics licensed under the Open Government Licence v.3.0

https://www.ons.gov.uk/methodology/geography/licences
