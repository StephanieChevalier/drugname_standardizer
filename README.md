# Drugname Standardizer

The **Drugname Standardizer** is a Python package and CLI tool for standardizing drug names using [the FDA's official UNII Names List archive](https://precision.fda.gov/uniisearch/archive). It supports both JSON and TSV/CSV input formats and is designed for easy integration in data processing pipelines.

![flowchart](https://raw.githubusercontent.com/StephanieChevalier/drugname_standardizer/main/img/flowchart_alpha.png)

---

## Features

- ✅ **Reliable source of synonyms**: the tool automatically downloads the latest `UNII Names` file from [the official FDA repository](https://precision.fda.gov/uniisearch/archive/latest/UNIIs.zip) and caches it locally (monthly freshness check).

- ✅ **Standardizes drug identifiers** (code, official, systematic, common, brand names) **to a single preferred name** using the *Display Name* field of the `UNII Names` file.

- ✅ **Multiple input types supported**:
   - A single drug name
   - A list of names (Python)
   - A JSON file with a list of names
   - A TSV/CSV file with a column of names

- ✅ **Python package interface** *(OOP style)* and **CLI interface** *(via `drugname-standardizer` command)*

- ✅ **Ambiguity resolution**: for entries with multiple *display names* in the FDA's UNII Names file, the shortest one is chosen. Rare but exists: 55 / 986397 associations in `UNII_Names_20Dec2024.txt`. For example, for `PRN1008` the ambiguity is solved by keeping `RILZABRUTINIB` whereas 2 associations exist:
   - `PRN1008`	...	... `RILZABRUTINIB, (.ALPHA.E,3S)-`
   - `PRN1008`	...	... `RILZABRUTINIB`  

> ⚠️ There are code / official / systematic / common / brand names for drugs. Some are linked to different level of details about the compound.
**This tool favors "high-level" naming** (i.e. the less detailled one) : detailed systematic or branded names are mapped to a standardized, less verbose preferred name (as defined by the FDA Display Name field). For instance : both `3'-((1R)-1-((6R)-5,6-DIHYDRO-4-HYDROXY-2-OXO-6-PHENETHYL-6-PROPYL-2H-PYRAN-3-YL)PROPYL)-5-(TRIFLUOROMETHYL)-2-PYRIDINESULFONANILIDE` (systematic name) and `Aptivus` (brand name) become `TIPRANAVIR`.

---

## Python API

You can use the package programmatically in your Python scripts:

### Usage

```python
from drugname_standardizer import DrugStandardizer
ds = DrugStandardizer()
```

#### Standardize a single name
```python
print(ds.standardize_name("GDC-0199"))  # → VENETOCLAX
```

#### Standardize a list of names
```python
names = ["aptivus", "gdc-0199"]
print(ds.standardize_list(names))  # → ['TIPRANAVIR', 'VENETOCLAX']
```

#### 📄 Standardizing a JSON file
```python
from drugname_standardizer import DrugStandardizer

ds = DrugStandardizer()
ds.standardize_json_file("drugs.json")
```

This will:

* read a list of drug names from `drugs.json`,
* standardize each name to its preferred form (based on the FDA Display Name),
* save the result as `drugs_drug_standardized.json` by default.

You can optionally specify an output filename with `output_path=...`.

#### 📄 Standardizing a TSV/CSV file

```python
ds.standardize_tsv_file(
    input_path="dataset.csv",
    column_drug=0,
    separator=","
)
```

* The column at index `0` (1st column) will be standardized.
* The result will be saved as `dataset_drug_standardized.csv` by default.
* You can customize the output name using the `output_path` parameter.

---

## Command-Line Interface (CLI)

Once installed, you can use the CLI tool directly:

### Basic syntax

```bash
drug-standardizer -i INPUT [options]
```

### Required:

* `--input`, `-i`: a drug name or path to a file (JSON/TSV)

### Optional:

| Option                | Description                                                     |
| --------------------- | --------------------------------------------------------------- |
| `--file_type`, `-f`   | Type of the input file: `"json"` or `"tsv"`                     |
| `--output`, `-o`      | Output filename (optional, default: auto-generated)             |
| `--column_drug`, `-c` | Column index with drug names for TSV input (starts at 0)        |
| `--separator`, `-s`   | Separator for TSV files (default: `\t`)                         |
| `--unii_file`, `-u`   | Custom UNII Names file path (optional, overrides auto-download) |

### CLI examples

* Standardize a drug name:

  ```bash
  drugname-standardizer -i GDC-0199
  ```

* 📄 Standardize a JSON list:

  ```bash
  drugname-standardizer -i drugs.json -f json
  ```
  The `-f json` flag is required so the CLI interprets the input file correctly.  
  If `-o` is not specified, the output will be saved as `drugs_drug_standardized.json` by default.

* 📄 Standardize a TSV file (e.g., drug names in column 2, pipe separator):

  ```bash
  drugname-standardizer -i dataset.tsv -f tsv -c 2 -s "|" -o standardized_dataset.tsv
  ```
  The `-f tsv` and `-c` flags are required for TSV/CSV files.  
  If `-o` is not specified, the output is saved as `dataset_drug_standardized.json` by default.

---

## Installation

### Using `pip`

```bash
pip install drugname_standardizer
```

### From source

```bash
git clone https://github.com/StephanieChevalier/drugname_standardizer.git
cd drugname_standardizer
pip install -r requirements.txt
```

> `drug-standardizer` will then be available as a CLI command.

### Requirements

* Python 3.7+
* Dependencies:
- Dependencies:
  - `requests >= 2`
  - `tqdm >= 4`

---

## How it works

1. **Parsing UNII File**:

   * Downloads and parses the latest `UNII_Names.txt` file
   * Maps all name variants to their associated *Display Name*
   * Resolves rare naming ambiguities (e.g., 55 ambiguous entries over \~986k)

2. **Standardizing names**:
   * For a single drug name: return the preferred name.
   * For a list of drug names: maps drug names to their preferred names and return the updated list.
   * For JSON input: Maps drug names to their preferred names and saves the results to a JSON file.
   * For TSV input: Updates the specified column with standardized drug names and saves the modified DataFrame to a TSV file.

---

## Package structure

```
drugname_standardizer/
├── drugname_standardizer/
│   ├── __init__.py               # Package initialization
│   ├── __main__.py               # CLI entry point
│   ├── standardizer.py           # Core logic for name standardization
│   └── data/
│       ├── UNII_Names.txt  # UNII Names List file (ensured to be no older than 1 month when available)
│       └── UNII_dict.pkl   # parsed UNII Names List
├── tests/
│   ├── __init__.py               
│   └── test_standardizer.py      # Unit tests for the package
├── LICENSE                       # MIT License
├── pyproject.toml                # Package configuration
├── README.md                     # Project documentation
└── requirements.txt              # Development dependencies
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/StephanieChevalier/drugname_standardizer/blob/main/LICENSE) file for details.
