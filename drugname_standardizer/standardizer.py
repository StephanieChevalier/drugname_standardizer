import json
import pandas as pd
from pathlib import Path
import requests
import zipfile
import pickle
import os
from tqdm import tqdm
from urllib.parse import urlparse, unquote
from datetime import datetime, timedelta

DEFAULT_UNII_FILE_PATH = Path(__file__).parent / "data"
#DEFAULT_UNII_FILE = Path(__file__).parent / "data" / "UNII_Names_20Dec2024.txt"
DOWNLOAD_URL = "https://precision.fda.gov/uniisearch/archive/latest/UNIIs.zip"

class DownloadError(Exception):
    """Custom exception for download-related issues."""
    pass

def download_unii_file(download_url: str = DOWNLOAD_URL, extract_to: Path = DEFAULT_UNII_FILE_PATH):
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

    try: # Download the ZIP file
        print("----------------------------------------------------------------------")
        print(f"Downloading UNII file from {download_url}...")

        response = requests.get(download_url, stream=True, timeout=30)  # Added timeout
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Parse the URL to remove query parameters and get the actual file name
        parsed_url = urlparse(response.url)
        filename = os.path.basename(parsed_url.path)
        # Decode URL-encoded characters (e.g., %20 -> space)
        filename = unquote(filename)

        # Path for the downloaded ZIP file
        zip_path = extract_to / filename
        #print(f"DEBUG: zip_path : {zip_path}")

        with open(zip_path, "wb") as f:
            total_size = int(response.headers.get('content-length', 0))
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as progress_bar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress_bar.update(len(chunk))

        #print(f"DEBUG: Download complete to {zip_path}.")

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
        # Extract only the file that starts with "UNII_Names"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the file that starts with "UNII_Names"
            for zip_info in zip_ref.infolist():
                if zip_info.filename.startswith("UNII_Names"):
                    unii_file_name = zip_info.filename
                    # Extract the specific file
                    #print(f"DEBUG: Downloaded UNII file : {unii_file_name}")
                    with zip_ref.open(unii_file_name) as source_file:
                        dest_file_path = extract_to / "UNII_Names.txt"
                        with open(dest_file_path, "wb") as dest_file:
                            dest_file.write(source_file.read())
                    #print(f"DEBUG: Extracted and copied content to {dest_file_path}")
                    break  # Stop once the file is found and processed
            else:
                print("No file starting with 'UNII_Names' found in the archive.")
    except zipfile.BadZipFile as e:
        raise DownloadError(f"The downloaded file is not a valid ZIP file. Details: {e}")
    finally:
        # Clean up the ZIP file
        if zip_path.exists():
            zip_path.unlink()
            #print(f"DEBUG: Removed temporary ZIP file: {zip_path}")
        if dest_file_path.exists():
            print(f"UNII Names file extracted to {dest_file_path}")
            print(f"----------------------------------------------------------------------")
            return dest_file_path

def parse_unii_file(file_path: str = None):
    """Parse the UNII source file to create a dictionary of drug name associations.

    Args:
        file_path (str, optional): Path to the UNII file.

    Returns:
        dict: A dictionary mapping drug names to their preferred names.

    Raises:
        FileNotFoundError: If a UNII path is given but the file does not exist.
    """
    dict_pickle_path = DEFAULT_UNII_FILE_PATH / "UNII_dict.pkl"

    if file_path: # If user gives a path, go for it and raise and error (with advice) if incorrect.
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(
                f"The UNII Names file you give as argument ({file_path}) does not exist or its path is invalid.\n"
                f"You can rerun the script without specifying it to automatically download the latest UNII Names file."
            )
    else: # If no precised path, search for a UNII_Names file in the folder
        # Filter files that start with "UNII_Names"
        path = DEFAULT_UNII_FILE_PATH
        path.mkdir(parents=True, exist_ok=True)
        for file in path.iterdir():
            if file.name.startswith("UNII_Names") and file.stat().st_size > 1000:
                # Get the last modification time
                modification_time = datetime.fromtimestamp(file.stat().st_mtime)
                # Calculate 3 months ago
                one_month_ago = datetime.now() - timedelta(days=30)
                if modification_time > one_month_ago:
                    file_path = file
                    if dict_pickle_path.exists():
                        with open(dict_pickle_path, "rb") as f_dict:
                            parsed_dict = pickle.load(f_dict)
                        return parsed_dict

    if file_path is None:
        print(f"Attempting to download the latest UNII file...")
        file_path = download_unii_file(extract_to=DEFAULT_UNII_FILE_PATH)

    print("Parsing of the UNII Names file...")
    with open(file_path, "r") as file:
        lines = file.readlines()

    header = lines[0].strip().split("\t")
    data_lines = [line.strip().split("\t") for line in lines[1:]]

    parsed_dict = {}

    # Add tqdm progress bar when iterating over data_lines
    for line in tqdm(data_lines, desc="Processing file data", unit="line"):
        name = line[0].upper()
        display_name = line[3].upper()
        if name not in parsed_dict:
            parsed_dict[name] = []
        if display_name not in parsed_dict[name]:
            parsed_dict[name].append(display_name)

    # for line in data_lines:
    #     name = line[0].upper()
    #     display_name = line[3].upper()
    #     if name not in parsed_dict:
    #         parsed_dict[name] = []
    #     if display_name not in parsed_dict[name]:
    #         parsed_dict[name].append(display_name)

    parsed_dict = resolve_ambiguities(parsed_dict)
    with open(dict_pickle_path, "wb") as f_dict:
        pickle.dump(parsed_dict, f_dict)
    return parsed_dict

def resolve_ambiguities(parsed_dict):
    """Resolve ambiguities by selecting the shortest preferred name."""
    return {name: min(values, key=len) if len(values) > 1 else values[0] for name, values in parsed_dict.items()}

# Functions to handle each input type
def standardize_name(drug_name, parsed_dict):
    """Standardize a single drug name."""
    return parsed_dict.get(drug_name.upper(), drug_name)

def standardize_list(drug_names, parsed_dict):
    """Standardize a list of drug names."""
    return [parsed_dict.get(name.upper(), name) for name in drug_names]

def standardize_json_file(input_file, output_file, parsed_dict):
    """Standardize drug names in a JSON file."""
    with open(input_file, "r") as f:
        drug_names = json.load(f)
    standardized_names = standardize_list(drug_names, parsed_dict)
    with open(output_file, "w") as f:
        json.dump(standardized_names, f, indent=4)
    print(f"Standardized JSON file saved as {output_file}")

def standardize_tsv_file(input_file, output_file, column_drug, separator, parsed_dict):
    """
    Standardize drug names in a TSV file.

    Args:
        input_file (str): Path to the input TSV file.
        output_file (str): Path to the output standardized TSV file.
        column_drug (int): The index of the column containing drug names.
        separator (str): Field separator used in the TSV file.
        parsed_dict (dict): Dictionary mapping drug names to standardized names.

    Raises:
        ValueError: If the column index is invalid or not specified.
    """
    df = pd.read_tsv(input_file, sep=separator)

    # Validate column index
    if column_drug is None or column_drug < 0 or column_drug >= len(df.columns):
        raise ValueError("The index of the column containing the drug name to standardize must be specified.")

    column_name = df.columns[column_drug]
    df[column_name] = df[column_name].apply(lambda x: parsed_dict.get(str(x).upper(), x))
    df.to_tsv(output_file, index=False, sep=separator)
    print(f"Standardized TSV file saved as {output_file}")



def standardize_tsv_file_line_by_line(input_file, output_file, column_drug, separator, parsed_dict):
    """
    Standardize drug names in a TSV file line by line.

    Args:
        input_file (str): Path to the input TSV file.
        output_file (str): Path to the output standardized TSV file.
        column_drug (int): The index of the column containing drug names.
        separator (str): Field separator used in the TSV file.
        parsed_dict (dict): Dictionary mapping drug names to standardized names.

    Raises:
        ValueError: If the column index is invalid.
    """
    total_size = os.path.getsize(input_file)

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        # Read the header to validate the column index and write it to output
        header = infile.readline()
        columns = header.split(separator)

        if column_drug is None or column_drug < 0 or column_drug >= len(columns):
            raise ValueError("The index of the column containing the drug name to standardize must be specified.")

        outfile.write(header)

        with tqdm(total=total_size, unit="B", unit_scale=True, desc="Standardization") as pbar:
            # Process the file line by line
            for line in infile:
                line = line.strip("\n")
                fields = line.split(separator)
                # Standardize the required column
                if column_drug < len(fields):
                    fields[column_drug] = parsed_dict.get(fields[column_drug].upper(), fields[column_drug])
                # Write the modified line to output
                outfile.write(separator.join(fields) + '\n')
                pbar.update(len(line.encode('utf-8')))  # Update progress by bytes processed

    print(f"Standardized TSV file saved as {output_file}")


# Wrapper function to handle various input types
def standardize(
    input_data,
    output_file=None,
    file_type=None,
    column_drug=None,
    separator="\t",
    unii_file=None,
    cli_mode=False
):
    """
    Standardize drug names using a dictionary derived from the FDA's UNII Names List.

    This function processes drug names provided as input and standardizes them using a
    mapping from the lattest FDA's UNII Names List. The input can be a single drug name,
    a list of drug names, or a file containing drug names (in JSON or TSV format).

    Args:
        input_data (str | list):
            The input data to process. This can be:
                - A string representing a single drug name.
                - A list of strings representing multiple drug names.
                - A file path (string) pointing to a JSON or TSV file containing drug names.
        output_file (str, optional):
            Path to save the standardized JSON/TSV output file. If not provided, a default
            name will be generated by appending "_drug_standardized" before the file extension.
            Only applicable if `input_data` is a file path. Ignored for single names or lists
        file_type (str, optional):
            Type of the input file, either "json" or "tsv". This is required if `input_data`
            is a file path. Ignored for single names or lists.
        column_drug (int, optional):
            For TSV input files, the index of the column containing drug names to standardize.
            Required if `file_type` is "tsv". Starts at 0: 1st column = column 0.
        separator (str, optional):
            Field separator for TSV files. Defaults to "\t". Only applicable if `file_type` is "tsv".
        unii_file (str, optional):
            Path to a UNII file containing the drug name mappings, if a particular prior version is
            preferred. Defaults to a pre-defined UNII file location where the automatic download of
            the lattest version ends.

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
            >>> standardize("GDC-0199")
            'VENETOCLAX'

        2. Standardizing a list of drug names:
            >>> standardize(["GDC-0199", "APTIVUS"])
            ['VENETOCLAX', 'TIPRANAVIR']

        3. Standardizing drug names in a JSON file:
            >>> standardize(
                    input_data="drugs.json",
                    file_type="json",
                    output_file="standardized_drugs.json"
                )

        4. Standardizing drug names in a TSV file:
            >>> standardize(
                    input_data="drugs.tsv",
                    file_type="tsv",
                    column_drug=0,
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

    elif isinstance(input_data, str) and file_type == "tsv":
        if output_file is None:
            input_path = Path(input_data)
            output_file = input_path.with_name(input_path.stem + "_drug_standardized" + input_path.suffix)
        standardize_tsv_file_line_by_line(input_data, output_file, column_drug, separator, parsed_dict)

    elif isinstance(input_data, list):
        return standardize_list(input_data, parsed_dict)

    elif isinstance(input_data, str):
        standardized_name = standardize_name(input_data, parsed_dict)
        if cli_mode:
            print(f"Standardized drug name: {standardized_name}")
        return standardized_name

    else:
        raise ValueError("Unsupported input type. Provide a drug name, a list of drug names, or a valid file path to a JSON or a TSV file.")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Standardize drug names using the official FDA UNII Names List archive.")
    parser.add_argument("-i", "--input", required=True, help="Input file path (JSON or TSV).")
    parser.add_argument("-o", "--output", help="Output file path. Defaults to input file name with '_drug_standardized' before the extension.")
    parser.add_argument("-f", "--file_type", choices=["json", "tsv"], required=False, help="Type of input file.")
    parser.add_argument("-c", "--column_drug", type=int, help="Index of the column containing the drug names to standardize (starts at 0: 1st column = column 0). Required for TSV input.")
    parser.add_argument("-s", "--separator", type=str, default="\t", help="Field separator for TSV input. Defaults to '\t'.")
    parser.add_argument("-u", "--unii_file", default=None, help="Path to the UNII file.")

    args = parser.parse_args()

    # Call the standardize function with the appropriate arguments
    standardize(
        input_data=args.input,
        output_file=args.output,
        file_type=args.file_type,
        column_drug=args.column_drug,
        separator=args.separator,
        unii_file=args.unii_file,
        cli_mode=True,
    )

if __name__ == "__main__":
    main()
