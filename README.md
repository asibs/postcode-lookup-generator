# Postcode Lookup Generator

If you just need a _simple_ lookup from postcode to _most likely_ constituency, you can download a CSV from the folks
at mySociety:

https://www.mysociety.org/2023/09/12/navigating-the-new-constituencies/

Or use https://mapit.mysociety.org/ which includes Northern Ireland postcodes.

If you care about the fact that _some_ postcodes may straddle multiple constituencies (ie. _sometimes_ not all
addresses in a single postcode are in the same constituency), then read on...

## Shut up and give me the data!

### CSV file

[/data/2024-01-28/output/postcode-lookup.csv](https://github.com/asibs/postcode-lookup-generator/blob/main/data/2024-01-28/output/postcode-lookup.csv)

Contains a row for each postcode (postcodes are stripped of any whitespace), and which constituencies we think the
postcode falls within. The constituency columns, `pcon_1`, etc contain the mySociety constituency short code. You can
use this code to map to other constituency codes (eg. GSS code, etc) using the
[mySociety dataset here](https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.csv).

If a postcode is in more than one constituency, the `pcon_1` column will contain the constituency code we are _most
confident_ of / the constituency we believe _most_ addresses in the postcode are in.

### SQLite database file

[/data/2024-01-28/output/postcode-lookup.db](https://github.com/asibs/postcode-lookup-generator/blob/main/data/2024-01-28/output/postcode-lookup.db)

Use the following example to get all constituencies which contain part of the given postcode, ordered by confidence
(highest confidence first):

```sql
SELECT
  pcon.slug,
  pcon.short_code,
  pcon.name,
  postcode_lookup.confidence
FROM postcode_lookup
JOIN pcon ON postcode_lookup.pcon_id = pcon.id
WHERE postcode_lookup.postcode = 'AB101QJ'
ORDER BY postcode_lookup.confidence DESC;
```

If you just want the most likely constituency for a given postcode, simply add a `LIMIT 1`.

Note, you must normalise the postcode input by uppercasing and removing any whitespace.

## More background

### The problem

_Most_ postcodes in the UK are all within a single Westminster constituency, but _some_ straddle 2 (or more!). This
means that _some_ addresses in a postcode are in constituency A, and _some_ are in constituency B (and maybe some are
in constituency C, D, E, etc!).

The same problem exists for other boundaries, such as councils, council wards, etc.

Many people and websites want a simple way for people to find out which constituency they live in (or which council,
which ward, etc).

Historically, creating an _accurate_ postcode lookup to tell a user their constituency (or council, ward, etc) has
been extremely difficult, or maybe impossible, without paying a lot of money for
[licensed postcode data](https://www.ordnancesurvey.co.uk/products/code-point-polygons).

### Historical approaches

Historically, open data has existed for:

- Political boundaries - ie. the complete area covered by constituencies, councils, wards, etc
- Postcode _centroids_ - ie. just the centre-point of a postcode (not the full area covered by a postcode)

With these two pieces of open data, a number of approaches can be taken to mapping postcode to constituency:

1. Assume _all_ households within a postcode are in the constituency which overlaps with the postcode centroid
    - This gives incorrect information to some people, and it doesn't attempt to detect which postcodes _might_
      straddle multiple constituencies.
2. Check for all constituencies within a radius of X around the postcode centroid. If there's only one, assume all
  addresses in the postcode are within that single constituency. If there are multiple constituencies, you can prompt
  users to select their constituency from a list of the possible options.
    - This will still give incorrect information to some people, because the boundary of a postcode may fall outside the
      radius you specify. It may also give many false-positives of uncertainty because postcodes have very big variations
      in size depending on the population density of the area.
3. The most complex approach has involved trying to [reverse-engineer (very) _approximate_ postcode boundaries from
  _just_ the postcode centroids](https://longair.net/blog/2017/07/10/approximate-postcode-boundaries/). Using these
  (very) approximate boundaries, you can then look for postcodes which overlap with multiple constituencies.
    - Even this approach still has false-positives and false-negatives, but was probably the best possible without more
      open data.

_Note_: The great people at [Democracy Club](https://democracyclub.org.uk/) do in fact solve this problem with (I
believe) 100% accuracy, but I _believe_ they can only do so by having access to some non-open data which powers their
'Polling Station finder' tool. For example, they must have access to the mapping of each UK address to the polling
station for that address, and presumably from there they can map to a single ward, constituency, council, for that
polling station.

### New open data, new approach

New data spotted by [Mark Longair](https://longair.net/blog/2021/08/23/open-data-gb-postcode-unit-boundaries/) was
released in 2020 - a postcode column was added to the National Statistics UPRN Lookup dataset.

This dataset now includes:

- Every UPRN (an identifier for each building with an address in the UK)
- The postcode for each UPRN
- The location of each UPRN (OS Grid Easting/Northing)

Using this dataset, we can work out which constituency every address (UPRN) falls into by taking the location and
seeing which constituency it overlaps with.

If every UPRN in a single postcode is in the same constituency, we can assume that the whole postcode is within that
constituency.

If different UPRNs within a single postcode have different constituencies, we know we might have a postcode where the exact
address is needed to determine the constituency. As the open UPRN data includes non-address UPRNs such as Street Records,
with no classification, it is possible for every address in the postcode to be in one constituency, but for all the UPRNs
to cover more than one constituency.

At the time of writing, there's no open data source which maps UPRNs to a human-readable address. This means if a
user's postcode straddles multiple constituencies, we can now detect it and tell the user (possibly asking them to
select from a list of possible constituencies), we still can't tell them their constituency. If we had the UPRN to
human-readable address mapping, we could display the list of addresses for their postcode, and once they've
selected their address, show them their exact constituency.

_Caveat: All of the above assumes the single-point location we have for each UPRN accurately determines the
constituency. It is possible that for a small proportion of properties this isn't the case - eg. a large property
straddles the boundaries of 2 constituencies, the property centroid in the UPRN Lookup is in constituency A, but
officially the property is in constituency B. In practice we assume this is unlikely, but you could add a fudge
factor - ie. for each property, search for all constituencies within X meters of the property, rather than
just those which contain it. This would significantly increase the time taken by the install steps below, as the
PostGIS queries would become significantly more expensive._

## Installation

If you wish to build the data yourself, eg to do ad-hoc analysis with the PostGIS database, or to add extra data to the
resulting CSV / SQLite database, you can run the postcode lookup generator code yourself.

### Pre-requisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Python 3.12 (I recommend using [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv) to install
  & manage python versions)
- [Poetry](https://python-poetry.org/docs/#installation)
- [Docker](https://docs.docker.com/desktop/install/linux-install/)
- The ogr2ogr command-line tool for converting geospatial data to different formats - [this link seems to be most
  helpful for installation advice](https://mapscaping.com/installing-gdal-for-beginners/)
- The install will be much easier if you can run Makefiles. If you use Mac or Unix you should already be able to run
  these. If you use Windows, you may be able to install a program to run them, or you may be able to manually run the
  commands in the `Makefile` one-by-one

### Source data

Get the source data. If the source data changes, a new dated folder will be created in `/data` with the instructions
for this version. If you want an older version of the source data, use the instructions in that folder.

The current version of the source data is `2024-01-28`, and the instructions to get this data are:

- Ensure you are in the `data/2024-01-28/` directory
- `wget -O input/mysociety_2025_constituencies.csv https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.csv`
- `wget -O input/mysociety_2025_constituencies_boundaries.gpkg https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.gpkg`
- Manually download the [UPRN data from here](https://geoportal.statistics.gov.uk/datasets/9e5789e21a374f4c91dc4fac976003dc/about), unzip, and copy the data files (`NSUL_JAN_2024_*.csv`) into the `input/ONS_UPRN_lookup` folder (this could probably be automated with a wget & gunzip combo)
- Manually download the [ONSPD data from here](https://geoportal.statistics.gov.uk/datasets/3700342d3d184b0d92eae99a78d9c7a3/about), unzip, and copy the data file (`ONSPD_NOV_2023_UK.csv`) into the `input/ONS_postcode_directory` folder (this could probably be automated with a wget & gunzip combo)

If you don't have the `wget` command line utility (eg. Windows) you can manually download the files and rename them appropriately.

### Install

```
git clone git@github.com:asibs/postcode-lookup-generator.git
cd postcode-lookup-generator
make clean_install
```

The repo will take some time to clone, as it contains large CSV input data files.

The install process will probably take an hour or more, as it copies all data into a dockerised PostGIS database, and
then performs various geo-spatial queries on _every single address_.

### Data Validation

We can do various data validation on the installed data:

```sql
-- Look for postcodes which are in the UPRN Lookup dataset, but which aren't in the mySociety dataset
SELECT DISTINCT postcode
FROM uprn_postcode_to_constituency uprn
WHERE NOT EXISTS (
  SELECT 1 FROM mysociety_postcode_to_constituency mysoc WHERE mysoc.postcode = uprn.postcode
);

-- Look for postcodes which are in the mySociety dataset, but which aren't in the UPRN Lookup dataset
SELECT DISTINCT postcode
FROM mysociety_postcode_to_constituency mysoc
WHERE NOT EXISTS (
  SELECT 1 FROM uprn_postcode_to_constituency uprn WHERE uprn.postcode = mysoc.postcode
);

-- Look for postcodes which are in the UPRN Lookup dataset, but which aren't in the ONSPD dataset
SELECT DISTINCT postcode
FROM uprn_postcode_to_constituency uprn
WHERE NOT EXISTS (
  SELECT 1 FROM onspd_postcode_to_constituency onspd WHERE onspd.postcode = uprn.postcode
);

-- Look for postcodes which are in the ONSPD dataset, but which aren't in the UPRN Lookup dataset
SELECT DISTINCT postcode
FROM onspd_postcode_to_constituency onspd
WHERE NOT EXISTS (
  SELECT 1 FROM uprn_postcode_to_constituency uprn WHERE uprn.postcode = onspd.postcode
);

-- Look for postcodes which are in the mySociety dataset AND in the UPRN Lookup dataset, where the constituency
-- identified by mySociety for that postcode has not been identified by our UPRN methodology
SELECT *
FROM mysociety_postcode_to_constituency mysoc
JOIN uprn_postcode_to_constituency uprn
ON mysoc.postcode = uprn.postcode
AND NOT EXISTS (
  SELECT 1 FROM uprn_postcode_to_constituency uprn
  WHERE uprn.postcode = mysoc.postcode
  AND uprn.constituency_code = mysoc.constituency_code
)
ORDER BY 1;

-- Look for postcodes which are in the ONSPD dataset AND in the UPRN Lookup dataset, where the constituency
-- identified by the ONSPD method has not been identified by our UPRN methodology
SELECT *
FROM onspd_postcode_to_constituency onspd
JOIN uprn_postcode_to_constituency uprn
ON onspd.postcode = uprn.postcode
AND NOT EXISTS (
  SELECT 1 FROM uprn_postcode_to_constituency uprn
  WHERE uprn.postcode = onspd.postcode
  AND uprn.constituency_code = onspd.constituency_code
)
ORDER BY 1;
```

If you find odd looking data, the following websites may be useful:

- [uprn.uk](https://uprn.uk/) - find a specific UPRN on a map, or find all UPRNs within a specific postcode
- [Electoral Calculus map of new constituecy boundaries](https://www.electoralcalculus.co.uk/openseatmap.html?seats=2023)

### Generate output files

Once the install is complete, you can generate output files, such as a postcode -> constituency CSV or SQLite database.

#### CSV file

Generate a CSV file with a single line for each postcode, and a column for each constituency we believe part of the
postcode falls within. For most postcodes, this will only be a single constituency. Where there are multiple
constituencies, they will be ordered by how confident we are that the given postcode (or part of it) falls within the
constituency, and how many addresses within the postcode are covered by the constituency.

`make generate_csv_postcode_lookup`

You can add confidence level columns (ranging from 0.0 to 1.0) to the CSV by editing the `scripts/generate_csv.py` file
and changing the `write_confidences` parameter to `True`. These confidences are only indicitave, and primarily intended
as to order the constituencies.


#### SQLite database file

Generate a SQLite database file with a row for each postcode to constituency mapping, including the confidence level.
For most postcodes, there will only be a single row (a single constituency). Where there are multiple constituencies,
the confidence column should be used to order the rows (descending) in order to return the constituency we're most
confident in first.

`make generate_sqlite_postcode_lookup`

### Ad-hoc analysis

You can connec to to the local dockerised PostGIS with:

`psql postgres://local:password@localhost:54321/gis`

From there you can explore the tables and do any ad-hoc analysis.

**TODO**: List the tables and schema

### Shutting down

- `make stop_db` - Stops the PostGIS docker database, but leaves all data intact (you can start it again with `make start_db`)
- `make delete_db` - Stops the PostGIS docker database, and **deletes the volume with all the data**.
