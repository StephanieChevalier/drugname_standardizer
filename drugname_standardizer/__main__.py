# __main__.py

import argparse
from pathlib import Path
from drugname_standardizer import DrugStandardizer

def main():
    parser = argparse.ArgumentParser(
        description="Standardize drug names using the official FDA UNII Names List archive."
    )

    parser.add_argument(
        "-i", "--input", required=True,
        help="Input: a drug name, a list of names in a JSON file, or a TSV file."
    )
    parser.add_argument(
        "-o", "--output", help="Output file path (for JSON/TSV only)."
    )
    parser.add_argument(
        "-f", "--file_type", choices=["json", "tsv"],
        help="Type of the input file. Required if input is a file."
    )
    parser.add_argument(
        "-c", "--column_drug", type=int,
        help="Index of the drug name column (only for TSV). Starts at 0."
    )
    parser.add_argument(
        "-s", "--separator", type=str, default="\t",
        help="Separator for TSV file (default: tab)."
    )
    parser.add_argument(
        "-u", "--unii_file", help="Path to a specific UNII file (optional)."
    )

    args = parser.parse_args()

    # Initialise la classe une seule fois
    standardizer = DrugStandardizer(unii_file=args.unii_file)

    input_path = Path(args.input)
    if input_path.exists():
        if args.file_type == "json":
            standardizer.standardize_json_file(input_path, args.output)
        elif args.file_type == "tsv":
            if args.column_drug is None:
                raise ValueError("Please specify --column_drug when using TSV input.")
            standardizer.standardize_tsv_file(input_path, args.column_drug, separator=args.separator, output_path=args.output)
        else:
            raise ValueError("Please specify --file_type (json or tsv) when using a file.")
    else:
        # L’entrée n'est pas un fichier, on traite comme nom de médicament simple
        result = standardizer.standardize_name(args.input)
        print(result)

if __name__ == "__main__":
    main()
