import json
import pandas as pd
from pathlib import Path
import os
import requests
import zipfile
import pickle

DEFAULT_UNII_FILE = Path(__file__).parent.parent / "data" / "UNII_Names_20Dec2024.txt"
DOWNLOAD_URL = "https://precision.fda.gov/uniisearch/archive/latest/UNIIs.zip"

class DownloadError(Exception):
    """Custom exception for download-related issues."""
    pass

def download_unii_file(download_url=DOWNLOAD_URL, extract_to=DEFAULT_UNII_FILE.parent):
    """
    Downloads and extracts the UNII file from the specified URL.

    Args:
        download_url (str): URL to download the UNII archive.
        extract_to (Path): Directory where the extracted file will be saved.

    Returns:
        Path: Path to the extracted UNII file.

    Raises:
        DownloadError: If the download fails due to network issues or server errors.
        FileNotFoundError: If the UNII file cannot be found after extraction.
    """
    # Ensure the target directory exists
    extract_to.mkdir(parents=True, exist_ok=True)

    # Path for the downloaded ZIP file
    zip_path = extract_to / "UNIIs.zip"

    try:
        # Download the ZIP file
        print("----------------------------------------------------------------------")
        print(f"Downloading UNII file from {download_url}...")
        response = requests.get(download_url, stream=True, timeout=30)  # Added timeout
        response.raise_for_status()  # Raise an HTTPError for bad responses
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {zip_path}")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Handle connection or timeout issues specifically
        raise DownloadError(
            f"Failed to download the UNII file due to network issues. "
            f"Please check your internet connection. \nError details: {e}"
        )
    except requests.exceptions.RequestException as e:
        # Handle other request-related issues
        raise DownloadError(
            f"Failed to download the UNII file from {download_url}. "
            f"Please verify that the FDA's download URL is still valid. \nError details: {e}"
        )

    try:
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted UNII file to {extract_to}")
    except zipfile.BadZipFile as e:
        raise DownloadError(f"The downloaded file is not a valid ZIP file. Details: {e}")
    finally:
        # Clean up the ZIP file
        if zip_path.exists():
            os.remove(zip_path)
            print(f"Removed temporary ZIP file: {zip_path}")

    # Find the UNII file in the extracted contents
    for file in extract_to.iterdir():
        if file.name.startswith("UNII_Names"):
            print(f"UNII file extracted to {file}")
            print("----------------------------------------------------------------------")
            return file

    # If no valid UNII file is found, raise an error
    raise FileNotFoundError("UNII file not found in the downloaded archive.")

def parse_unii_file(file_path=None):
    """Parse the UNII source file to create a dictionary of drug name associations.

    Args:
        file_path (str, optional): Path to the UNII file.

    Returns:
        dict: A dictionary mapping drug names to their preferred names.

    Raises:
        FileNotFoundError: If a UNII path is given but the file does not exist.
    """
    if file_path:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(
                f"The specified UNII file path '{file_path}' is invalid or does not exist. "
                f"You can rerun the script without specifying a file path to automatically download the latest UNII Names file."
            )
    else:
        file_path = DEFAULT_UNII_FILE

    if not file_path.exists():
        print(f"Attempting to download the latest UNII file...")
        file_path = download_unii_file()

    print("Parsing of the UNII Names file...")
    with open(file_path, "r") as file:
        lines = file.readlines()

    header = lines[0].strip().split("\t")
    data_lines = [line.strip().split("\t") for line in lines[1:]]

    parsed_dict = {}
    for line in data_lines:
        name = line[0].upper()
        display_name = line[3].upper()
        if name not in parsed_dict:
            parsed_dict[name] = []
        if display_name not in parsed_dict[name]:
            parsed_dict[name].append(display_name)

    parsed_dict = resolve_ambiguities(parsed_dict)
    return parsed_dict

def resolve_ambiguities(parsed_dict):
    """Resolve ambiguities by selecting the shortest preferred name."""
    return {name: min(values, key=len) if len(values) > 1 else values[0] for name, values in parsed_dict.items()}

# Functions to handle each input type
def standardize_drug_name(drug_name, parsed_dict):
    """Standardize a single drug name."""
    return parsed_dict.get(drug_name.upper(), drug_name)

def standardize_drug_names_list(drug_names, parsed_dict):
    """Standardize a list of drug names."""
    return [parsed_dict.get(name.upper(), name) for name in drug_names]

def standardize_json_file(input_file, output_file, parsed_dict):
    """Standardize drug names in a JSON file."""
    with open(input_file, "r") as f:
        drug_names = json.load(f)
    standardized_names = standardize_drug_names_list(drug_names, parsed_dict)
    with open(output_file, "w") as f:
        json.dump(standardized_names, f, indent=4)
    print(f"Standardized JSON file saved as {output_file}")

def standardize_csv_file(input_file, output_file, column_index, separator, parsed_dict):
    """
    Standardize drug names in a CSV file.

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to the output standardized CSV file.
        column_index (int): The index of the column containing drug names.
        separator (str): Field separator used in the CSV file.
        parsed_dict (dict): Dictionary mapping drug names to standardized names.

    Raises:
        ValueError: If the column index is invalid or not specified.
    """
    df = pd.read_csv(input_file, sep=separator)

    # Validate column index
    if column_index is None or column_index < 0 or column_index >= len(df.columns):
        raise ValueError("The index of the column containing the drug name to standardize must be specified.")

    column_name = df.columns[column_index]
    df[column_name] = df[column_name].apply(lambda x: parsed_dict.get(str(x).upper(), x))
    df.to_csv(output_file, index=False, sep=separator)
    print(f"Standardized CSV file saved as {output_file}")

# Wrapper function to handle various input types
def standardize_drug_names(
    input_data,
    output_file=None,
    file_type=None,
    column_index=None,
    separator=",",
    unii_file=None,
    cli_mode=False
):
    """
    Standardize drug names using a dictionary derived from the FDA's UNII Names List.

    This function processes drug names provided as input and standardizes them using a
    mapping from the lattest FDA's UNII Names List. The input can be a single drug name,
    a list of drug names, or a file containing drug names (in JSON or CSV format).

    Args:
        input_data (str | list):
            The input data to process. This can be:
                - A string representing a single drug name.
                - A list of strings representing multiple drug names.
                - A file path (string) pointing to a JSON or CSV file containing drug names.
        output_file (str, optional):
            Path to save the standardized JSON/CSV output file. If not provided, a default
            name will be generated by appending "_drug_standardized" before the file extension.
            Only applicable if `input_data` is a file path. Ignored for single names or lists
        file_type (str, optional):
            Type of the input file, either "json" or "csv". This is required if `input_data`
            is a file path. Ignored for single names or lists.
        column_index (int, optional):
            For CSV input files, the index of the column containing drug names to standardize.
            Required if `file_type` is "csv".
        separator (str, optional):
            Field separator for CSV files. Defaults to ",". Only applicable if `file_type` is "csv".
        unii_file (str, optional):
            Path to the UNII file containing the drug name mappings. Defaults to a pre-defined
            UNII file location where the automatic download ends.

    Returns:
        list | str | None:
            - For a single drug name: Returns the standardized drug name as a string.
            - For a list of drug names: Returns a list of standardized drug names.
            - For a file input: Saves the standardized output to a file and returns None.

    Raises:
        ValueError:
            - If the input type is unsupported.

    Examples:
        1. Standardizing a single drug name:
            >>> standardize_drug_names("GDC-0199")
            'VENETOCLAX'

        2. Standardizing a list of drug names:
            >>> standardize_drug_names(["GDC-0199", "APTIVUS"])
            ['VENETOCLAX', 'TIPRANAVIR']

        3. Standardizing drug names in a JSON file:
            >>> standardize_drug_names(
                    input_data="drugs.json",
                    file_type="json",
                    output_file="standardized_drugs.json"
                )

        4. Standardizing drug names in a CSV file:
            >>> standardize_drug_names(
                    input_data="drugs.csv",
                    file_type="csv",
                    column_index=0,
                    separator=",",
                )

    Notes:
        - If `input_data` is a file, the function reads the file, processes the drug names,
          and writes the results to the specified or default output file.
        - For lists or single names, the function operates in memory and returns the standardized names.
    """
    parsed_dict = parse_unii_file(unii_file)

    # Handle different input types
    if isinstance(input_data, str) and file_type == "json":
        if output_file is None:
            input_path = Path(input_data)
            output_file = input_path.with_name(input_path.stem + "_drug_standardized" + input_path.suffix)
        standardize_json_file(input_data, output_file, parsed_dict)

    elif isinstance(input_data, str) and file_type == "csv":
        if output_file is None:
            input_path = Path(input_data)
            output_file = input_path.with_name(input_path.stem + "_drug_standardized" + input_path.suffix)
        standardize_csv_file(input_data, output_file, column_index, separator, parsed_dict)

    elif isinstance(input_data, list):
        return standardize_drug_names_list(input_data, parsed_dict)

    elif isinstance(input_data, str):
        standardized_name = standardize_drug_name(input_data, parsed_dict)
        if cli_mode:
            print(f"Standardized drug name: {standardized_name}")
        return standardized_name

    else:
        raise ValueError("Unsupported input type. Provide a drug name, a list of drug names, or a valid file path to a JSON or a CSV file.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Standardize drug names using the official FDA UNII Names List archive.")
    parser.add_argument("-i", "--input", required=True, help="Input file path (JSON or CSV).")
    parser.add_argument("-o", "--output", help="Output file path. Defaults to input file name with '_drug_standardized' before the extension.")
    parser.add_argument("-f", "--file_type", choices=["json", "csv"], required=False, help="Type of input file.")
    parser.add_argument("-c", "--column_index", type=int, help="Column index for CSV input.")
    parser.add_argument("-s", "--separator", type=str, default=",", help="Field separator for CSV input. Defaults to ','.")
    parser.add_argument("-u", "--unii_file", default=None, help="Path to the UNII file.")

    args = parser.parse_args()

    # Call the standardize_drug_names function with the appropriate arguments
    standardize_drug_names(
        input_data=args.input,
        output_file=args.output,
        file_type=args.file_type,
        column_index=args.column_index,
        separator=args.separator,
        unii_file=args.unii_file,
        cli_mode=True,
    )

if __name__ == "__main__":
    main()
