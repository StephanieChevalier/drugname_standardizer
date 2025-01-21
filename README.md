# Drugname Standardizer

The **Drugname Standardizer** is a Python tool for standardizing drug names using [the official FDA's UNII Names List archive](https://precision.fda.gov/uniisearch/archive). It notably supports both JSON and TSV input formats, making it easy to ensure consistent drug naming in datasets.

---

## Features

- **A trusted source for drug synonyms** : the package automatically downloads the latest version of the *UNII Names* file from [the official FDA repository](https://precision.fda.gov/uniisearch/archive/latest/UNIIs.zip).
The `UNII_Names.txt` is saved to the package's `data/` folder for future use. The user can also choose to indicate another local *UNII Names* file if a particular version is preferred.

- **Parsing of the FDA's UNII Names List to map drug names** (code / official / systematic / common / brand names) **to a single preferred name** (i.e. the *Display Name* of the UNII Names file).

- Input versatility:
   - a single drug name,
   - a list of drug names,
   - a JSON input file (a list of drugs to standardize)
   - a TSV input file (a dataframe containing a column of drugs to standardize)

- Provides both **a Python package interface for scripting** and **a command-line interface (CLI) for direct use**.

- Resolves naming ambiguities of the FDA's UNII Names file by selecting the shortest *Display Names*. Rare but exists: 55 / 986397 associations in `UNII_Names_20Dec2024.txt`. For example, for `PRN1008` the ambiguity is solved by keeping `RILZABRUTINIB` whereas 2 associations exist:
   - `PRN1008`	...	... `RILZABRUTINIB, (.ALPHA.E,3S)-`
   - `PRN1008`	...	... `RILZABRUTINIB`  

### **Warning:**

There are code / official / systematic / common / brand names for drugs. **Some are linked to different level of details about the compound.**
**The standardization proposed here gathers information at the "upper" level (i.e. the less detailled one).** I relied on the "Preferred Substance Name" (= the *Display name* field) indicated in the correspondence table provided by the FDA.  
For instance : both `3'-((1R)-1-((6R)-5,6-DIHYDRO-4-HYDROXY-2-OXO-6-PHENETHYL-6-PROPYL-2H-PYRAN-3-YL)PROPYL)-5-(TRIFLUOROMETHYL)-2-PYRIDINESULFONANILIDE` (systematic name) and `Aptivus` (brand name) become `TIPRANAVIR`.

---

## Usage

### Python API

You can use the package programmatically in your Python scripts:

```python
from drugname_standardizer import standardize
```

#### Examples:

**- Get the preferred name for a specific drug:**
```python
drug_name = "GDC-0199"
preferred_name = standardize(drug_name)
print(preferred_name)  # Outputs: VENETOCLAX
```

**- Standardize a list of drugs:**
```python
drug_names = ["GDC-0199", "Aptivus", "diodrast"]
preferred_names = standardize(drug_names)
print(preferred_names)  # Outputs: ["VENETOCLAX", "TIPRANAVIR", "IODOPYRACET"]
```

**- Standardize a JSON file:**
```python
standardize(
    input_file="drugs.json",
    output_file="standardized_drugs.json",
    file_type="json"
)
# Outputs: Standardized JSON file saved as standardized_drugs.json
```

**- Standardize a TSV file:**
```python
standardize(
    input_file="dataset.tsv",
    file_type="tsv",
    column_drug=0
)
# Outputs: Standardized TSV file saved as dataset_drug_standardized.tsv
```

### Command-Line Interface

You can also use a CLI for standardizing JSON and TSV files.

* Required arguments:
    - `--input`, `-i`: **A drug name or the path to a JSON/TSV file**
* Optional arguments:
  - `--file_type`, `-f`: **Type of the input file** (`json` or `tsv`)
  - `--output`, `-o`: **The output file name** (relative path can be given). Defaults: the input file name with `_drug_standardized` added before the extension.
  - `--column_drug`, `-c`: **Index of the column containing the drug names to standardize** (required for TSV files). Starts at 0: 1st column = column 0.
  - `--separator`, `-s`: **Field separator for TSV files**. Defaults: `\t`.
  - `--unii_file`, `-u`: **Path to a UNII Names List file**. Defaults: automatic download of the latest version.

#### Examples:

**- Get the preferred name for a specific drug:**
```bash
drugname_standardizer -i "DynaCirc"
```

**- Standardize a JSON file:**
```bash
drugname_standardizer -i drugs.json -f json
```

**- Standardize a TSV file:**
e.g., using a comma as separator and a custom file name for the output:
```bash
drugname_standardizer -i dataset.tsv -f tsv -c 2 -s "," -o standardized_dataset.tsv
```

---

## Installation

### Using pip

```bash
python3 -m pip install drugname_standardizer
```

### GitHub repository

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

- Python 3.12+
- Dependencies:
  - `pandas >= 2.2.2`
  - `requests >= 2.32.2`
  - `tqdm >= 4.66.4`

---

## How it works

1. Parse UNII File:
    - Reads the UNII Names List to create a mapping of drug names to the *Display Name* (i.e. the preferred name).
    - Resolves potential naming conflicts by selecting the shortest *Display Name* (55 / 986397 associations).

2. Standardize Names:
    - For a single drug name: return the preferred name.
    - For a list of drug names: maps drug names to their preferred names and return the updated list.
    - For JSON input: Maps drug names to their preferred names and saves the results to a JSON file.
    - For TSV input: Updates the specified column with standardized drug names and saves the modified DataFrame to a TSV file.

---

## Package structure
```
drugname_standardizer/
├── drugname_standardizer/
│   ├── __init__.py               # Package initialization
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

This project is licensed under the MIT License - see the [LICENSE](https://github.com/StephanieChevalier/drugname_standardizer/blob/main/LICENSE) file for details.
