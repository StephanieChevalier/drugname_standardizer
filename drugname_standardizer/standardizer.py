# drug_standardizer.py

import json
import os
import pickle
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests
from tqdm import tqdm

DEFAULT_UNII_FILE_PATH = Path(__file__).parent / "data"
DOWNLOAD_URL = "https://precision.fda.gov/uniisearch/archive/latest/UNIIs.zip"


class DownloadError(Exception):
    """Custom exception for download-related issues."""
    pass


class DrugStandardizer:
    def __init__(self, unii_file: str = None):
        """
        Initialize the standardizer by loading the mapping dictionary.
        If a precomputed pickle exists and is recent, it will be used.
        Otherwise, the raw UNII file will be parsed.

        Args:
            unii_file (str, optional): Path to a specific UNII file. Defaults to automatic detection/download.
        """
        self.unii_file_path = Path(unii_file) if unii_file else None
        self.parsed_dict = self._load_mapping()

    def _load_mapping(self):
        dict_pickle_path = DEFAULT_UNII_FILE_PATH / "UNII_dict.pkl"

        # Try to load from pickle if recent enough
        if self.unii_file_path is None:
            for file in DEFAULT_UNII_FILE_PATH.iterdir():
                if file.name.startswith("UNII_Names") and file.stat().st_size > 1000:
                    modification_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if modification_time > datetime.now() - timedelta(days=30):
                        self.unii_file_path = file
                        break

        if dict_pickle_path.exists():
            try:
                with open(dict_pickle_path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                pass  # fallback to parsing

        if self.unii_file_path is None or not self.unii_file_path.exists():
            print("No valid UNII file found. Attempting to download the latest version...")
            self.unii_file_path = self._download_unii_file()

        return self._parse_unii_file(self.unii_file_path, dict_pickle_path)

    def _download_unii_file(self):
        extract_to = DEFAULT_UNII_FILE_PATH
        extract_to.mkdir(parents=True, exist_ok=True)

        response = requests.get(DOWNLOAD_URL, stream=True, timeout=30)
        response.raise_for_status()

        filename = unquote(os.path.basename(urlparse(response.url).path))
        zip_path = extract_to / filename

        with open(zip_path, "wb") as f:
            total_size = int(response.headers.get('content-length', 0))
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as bar:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
                    bar.update(len(chunk))

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for zip_info in zip_ref.infolist():
                if zip_info.filename.startswith("UNII_Names"):
                    with zip_ref.open(zip_info.filename) as source_file:
                        dest_path = extract_to / "UNII_Names.txt"
                        with open(dest_path, "wb") as dest_file:
                            dest_file.write(source_file.read())
                    zip_path.unlink()
                    return dest_path

        raise DownloadError("No UNII_Names file found in archive.")

    def _parse_unii_file(self, file_path, dict_pickle_path):
        print("Parsing UNII file...")
        with open(file_path, "r") as f:
            lines = f.readlines()

        header = lines[0].strip().split("\t")
        data_lines = [line.strip().split("\t") for line in lines[1:]]

        parsed_dict = {}
        for line in tqdm(data_lines, desc="Building dictionary", unit="line"):
            name = line[0].upper()
            display_name = line[3].upper()
            if name not in parsed_dict:
                parsed_dict[name] = []
            if display_name not in parsed_dict[name]:
                parsed_dict[name].append(display_name)

        resolved = self._resolve_ambiguities(parsed_dict)

        with open(dict_pickle_path, "wb") as f:
            pickle.dump(resolved, f)

        return resolved

    def _resolve_ambiguities(self, parsed_dict):
        return {k: min(v, key=len) if len(v) > 1 else v[0] for k, v in parsed_dict.items()}

    def standardize_name(self, drug_name: str) -> str:
        return self.parsed_dict.get(drug_name.upper(), drug_name)

    def standardize_list(self, drug_list: list[str]) -> list[str]:
        return [self.standardize_name(name) for name in drug_list]

    def standardize_json_file(self, input_path, output_path=None):
        with open(input_path, "r") as f:
            data = json.load(f)

        standardized = self.standardize_list(data)

        if output_path is None:
            output_path = Path(input_path).with_stem(Path(input_path).stem + "_drug_standardized")

        with open(output_path, "w") as f:
            json.dump(standardized, f, indent=4)
        print(f"Saved: {output_path}")

    def standardize_tsv_file(self, input_path, column_drug, separator="\t", output_path=None):
        input_path = Path(input_path)
        if output_path is None:
            output_path = input_path.with_stem(input_path.stem + "_drug_standardized")

        total_size = os.path.getsize(input_path)

        with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
            header = infile.readline()
            columns = header.strip().split(separator)
            outfile.write(header)

            with tqdm(total=total_size, unit="B", unit_scale=True, desc="Standardizing TSV") as bar:
                for line in infile:
                    line = line.strip("\n")
                    fields = line.split(separator)
                    if column_drug < len(fields):
                        fields[column_drug] = self.standardize_name(fields[column_drug])
                    outfile.write(separator.join(fields) + "\n")
                    bar.update(len(line.encode("utf-8")))

        print(f"Saved: {output_path}")
