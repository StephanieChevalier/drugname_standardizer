# Drugname Standardizer

The **Drugname Standardizer** is a Python tool for standardizing drug names using [the official FDA's UNII Names List archive](https://precision.fda.gov/uniisearch/archive). It notably supports both JSON and CSV input formats, making it easy to ensure consistent drug naming in datasets.

---

## Features

### A trusted source for drug synonyms
- Default UNII File:  
**Automatically downloads the latest UNII file from the FDA's official archive if not already present in `drugname_standardizer/data/` folder.**  
*(https://precision.fda.gov/uniisearch/archive/latest/UNIIs.zip &rarr; UNII_Names_20Dec2024.txt)*
- Custom UNII File:  
**Users can download a UNII Names List file themselves from the FDA's UNII Archive** and specify its path.

### Key points
- **Parses the FDA UNII Names List to map drug names** (code / official / systematic / common / brand names) **to a single preferred name** (i.e. the *Display Name* of the UNII Names file).
- Input versatility by directly handling:
   - a single drug name,
   - a list of drug names,
   - a JSON input file (a list of drugs to standardize)
   - a CSV input file (a dataframe containing a column of drugs to standardize)
- Provides both **a Python package interface for scripting** and **a command-line interface (CLI) for ease of use**.
- Resolves naming ambiguities by selecting the shortest name if several *Display Names*.  
(a few cases in the UNII file: 55 among 986397 associations in version December 2024)


---

## Usage

### Python API

You can use the package programmatically in your Python scripts:

```python
from drugname_standardizer.standardizer import standardize_drug_names

# Get the preferred name for a specific drug
drug_name = "GDC-0199"
preferred_name = standardize_drug_names(drug_name)
print(preferred_name)  # Outputs: VENETOCLAX

# Get the preferred names for a list of drugs
drug_names = ["GDC-0199", "Aptivus", "diodrast"]
preferred_name = standardize_drug_names(drug_names)
print(preferred_name)  # Outputs: ["VENETOCLAX", "TIPRANAVIR", "IODOPYRACET"]

# Standardize a JSON file
standardize_drug_names(
    input_file="drugs.json",
    output_file="standardized_drugs.json",
    file_type="json"
) # Outputs: Standardized JSON file saved as standardized_drugs.json

# Standardize a CSV file
standardize_drug_names(
    input_file="dataset.csv",
    file_type="csv",
    column_index=1
) # Outputs: Standardized CSV file saved as dataset_drug_standardized.csv
```

### Command-Line Interface

You can also use a CLI for standardizing JSON and CSV files. Run the following command:

```bash
drugname_standardizer --input <input_file> --file_type <file_type> [options]
```

#### Required Arguments:
- `--input`: Path to the input file (JSON or CSV).
- `--file_type`: Type of the input file. Accepted values: `json`, `csv`.

#### Optional Arguments:
- `--output`: Path to the output file. Defaults to the input file name with `_drug_standardized` added before the extension.
- `--column_index`: Index of the column containing the drug names to standardize (required for CSV files).
- `--separator`: Field separator for CSV files. Defaults to `,`.
- `--unii_file`: Path to the UNII Names List file. Defaults: automatic download of the latest.


#### Example usage

##### Standardize a JSON file
```bash
drugname_standardizer --input drugs.json --file_type json
```
##### Standardize a CSV file

- using a custom separator and outputfile name
```bash
drugname_standardizer --input drugs.csv --file_type csv --column_index 2 --separator "\t" --output standardized_drugs.csv
```
- using a local UNII file version
```bash
drugname_standardizer --input drugs.csv --file_type csv --column_index 0 --unii_file UNII_Names_20Dec2024.txt
```

---

## Automatic download of the UNII file

**If the required UNII file is not found locally, the package automatically downloads the latest version from the FDA's official repository.** The file is saved to the package's `data/` directory for future use.

You can also manually trigger the download by calling:

```python
from drugname_standardizer.standardizer import download_unii_file

download_unii_file()
```

---

## Installation

### Clone the repository and install the dependencies:

```bash
git clone https://github.com/StephanieChevalier/drugname_standardizer.git
cd drugname_standardizer
pip install -r requirements.txt
```
<!--
### Install the package via `pip`:

```bash
pip install drugname_standardizer
```
-->

### Requirements:

- Python 3.7+
- Dependencies:
  - `pandas`
  - `requests`

---

## How it works

1. Parse UNII File:
    - Reads the UNII Names List to create a mapping of drug names to the *Display Name* (i.e. the preferred name).
    - Resolves potential naming conflicts by selecting the shortest *Display Name* (55 / 986397 associations).

2. Standardize Names:
    - For a single drug name: return the preferred name
    - For a list of drug names: maps drug names to their preferred names and return the updated list.
    - For JSON input: Maps drug names to their preferred names and saves the results to a JSON file.
    - For CSV input: Updates the specified column with standardized drug names and saves the modified DataFrame to a CSV file.

---

## Package structure
```
drugname_standardizer/
├── data/
│   └── UNII_Names_20Dec2024.txt  # Default UNII Names List file
├── drugname_standardizer/
│   ├── __init__.py               # Package initialization
│   ├── standardizer.py           # Core logic for name standardization
├── tests/
│   ├── __init__.py               # Marks the tests directory as a package
│   └── test_standardizer.py      # Unit tests for the package
├── LICENSE                       # MIT License
├── README.md                     # Project documentation
├── requirements.txt              # Development dependencies
└── pyproject.toml                # Consolidated package configuration
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
