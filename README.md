# Postcode Lookup Generator

If you just need a _simple_ lookup from postcode to _most likely_ constituency, you can download a CSV from the folks
at MySociety:

https://pages.mysociety.org/2025-constituencies/datasets/uk_parliament_2025_postcode_lookup/latest

If you care about the fact that _some_ postcodes may straddle multiple constituencies (ie. _sometimes_ not all
addresses in a single postcode are in the same constituency), then read on...

## Shut up and give me the data!

TODO: Link to the latest CSV

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
(licensed postcode data)[https://www.ordnancesurvey.co.uk/products/code-point-polygons].

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
3. The most complex approach has involved trying to (reverse-engineer (very) _approximate_ postcode boundaries from
  _just_ the postcode centroids)[https://longair.net/blog/2017/07/10/approximate-postcode-boundaries/]. Using these
  (very) approximate boundaries, you can then look for postcodes which overlap with multiple constituencies.
  - Even this approach still has false-positives and false-negatives, but was probably the best possible without more
    open data.

_Note_: The great people at (Democracy Club)[https://democracyclub.org.uk/] do in fact solve this problem with (I
believe) 100% accuracy, but I _believe_ they can only do so by having access to some non-open data which powers their
'Polling Station finder' tool. For example, they must have access to the mapping of each UK address to the polling
station for that address, and presumably from there they can map to a single ward, constituency, council, for that
polling station.

### New open data, new approach

New data spotted (Mark Longair)[https://longair.net/blog/2021/08/23/open-data-gb-postcode-unit-boundaries/] was
released in 2020 - a postcode column was added to the National Statistics UPRN Lookup dataset.

This dataset now includes:

- Every UPRN (an identifier for each building with an address in the UK)
- The postcode for each UPRN
- The location of each UPRN (OS Grid Easting/Northing)

Using this dataset, we can work out which constituency every address (UPRN) falls into by taking the location and
seeing which constituency it overlaps with.

If every UPRN in a single postcode is in the same constituency, we can assume that the whole postcode is within that
constituency.

If different UPRNs within a single postcode have different constituencies, we know we have a postcode where the exact
address is needed to determine the constituency.

TODO: Determine if it's possible to get the human-readable address for each UPRN as open data. With this, we could go
one step further, and for such postcodes ask users for their full address so we can determine their constituency.

## Installation

If you wish to build the data yourself, eg to do ad-hoc analysis with the PostGIS database, or to add extra data to the
resulting CSV / SQLite database, you can run the postcode lookup generator code yourself.

### Pre-requisites

- (Git)[https://git-scm.com/book/en/v2/Getting-Started-Installing-Git]
- (Git LFS)[https://github.com/git-lfs/git-lfs?utm_source=gitlfs_site&utm_medium=installation_link&utm_campaign=gitlfs#installing]
- Python 3.12 (I recommend using (pyenv)[https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv] to install
  & manage python versions)
- (Poetry)[https://python-poetry.org/docs/#installation]
- (Docker)[https://docs.docker.com/desktop/install/linux-install/]
- The ogr2ogr command-line tool for converting geospatial data to different formats - (this link seems to be most
  helpful for installation advice)[https://mapscaping.com/installing-gdal-for-beginners/]
- The install will be much easier if you can run Makefiles. If you use Mac or Unix you should already be able to run
  these. If you use Windows, you may be able to install a program to run them, or you may be able to manually run the
  commands in the `Makefile` one-by-one

### Source data

Get the source data. If the source data changes, a new dated folder will be created in `/data` with the instructions
for this version. If you want an older version of the source data, use the instructions in that folder.

The current version of the source data is `2024-01-28`, and the instructions to get this data are:

- Ensure you are in the `data/2024-01-28/` directory
- `wget -O mysociety_2025_constituencies.csv https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.csv`
- `wget -O mysociety_2025_constituencies_boundaries.gpkg https://pages.mysociety.org/2025-constituencies/data/parliament_con_2025/0.1.4/parl_constituencies_2025.gpkg`
- Manually download the UPRN lookup from here, unzip, and copy the data files (`NSUL_JAN_2024_*.csv`) into the `ONS_UPRN_lookup` folder (this could probably be automated with a wget & gunzip combo)

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

### Generate output files

Once the install is complete, you can generate output files, such as a postcode -> constituency CSV or SQLite database.

**TODO**: Add scripts to generate a SQLite & CSV file of postcode mappings & instructions on use

### Ad-hoc analysis

You can connec to to the local dockerised PostGIS with:

`psql postgres://local:password@localhost:54321/gis`

From there you can explore the tables and do any ad-hoc analysis.

**TODO**: List the tables and schema

### Shutting down

- `make stop_db` - Stops the PostGIS docker database, but leaves all data intact (you can start it again with `make start_db`)
- `make delete_db` - Stops the PostGIS docker database, and deletes the volume with all the data