# Postcode Lookup Generator

If you just need a _simple_ lookup from postcode to _most likely_ constituency, you can download a CSV from the folks
at MySociety:

https://pages.mysociety.org/2025-constituencies/datasets/uk_parliament_2025_postcode_lookup/0_1_2

If you care about the fact that _some_ postcodes may straddle multiple constituencies (ie. _sometimes_ not all
addresses in a single postcode are in the same constituency), then this tool might help you...

## Installation

### Pre-requisites

- Python 3.12 (I recommend using (pyenv)[https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv] to install
  & manage python versions)
- (Poetry)[https://python-poetry.org/docs/#installation]
- (Docker)[https://docs.docker.com/desktop/install/linux-install/]
- The ogr2ogr command-line tool for converting geospatial data to different formats - (this link seems to be most
  helpful for installation advice)[https://mapscaping.com/installing-gdal-for-beginners/]
- The install will be much easier if you can run Makefiles. If you use Mac or Unix you should already be able to run
  these. If you use Windows, you may be able to install a program to run them, or you may be able to manually run the
  commands in the `Makefile` one-by-one

### Install

```
git clone git@github.com:asibs/postcode-lookup-generator.git
cd postcode-lookup-generator
make clean_install
```

## TODO:

- Add instructions on connecting to postgis after install
- Add a separate script to generate a SQLite & CSV file of postcode mappings