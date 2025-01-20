import unittest
import os
import json
import pandas as pd
from io import StringIO
from pathlib import Path
from drugname_standardizer.standardizer import parse_unii_file, standardize, resolve_ambiguities, download_unii_file, DownloadError


class TestDrugnameStandardizer(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.temp_files = []  # Track temporary files to remove them later

        self.test_dict = parse_unii_file()
        # # Simulate a parsed UNII dictionary
        # self.test_dict = {
        #     "4-(4-((2-(4-CHLOROPHENYL)-4,4-DIMETHYL-1-CYCLOHEXEN-1-YL)METHYL)-1-PIPERAZINYL)-N-((3-NITRO-4-(((TETRAHYDRO-2H-PYRAN-4-YL)METHYL)AMINO)PHENYL)SULFONYL)-2-(1H-PYRROLO(2,3-B)PYRIDIN-5-YLOXY)BENZAMIDE": "VENETOCLAX",
        #     "4-(4-((2-(4-CHLOROPHENYL)-4,4-DIMETHYLCYCLOHEX-1-EN-1-YL)METHYL)PIPERAZIN-1-YL)-N-((3-NITRO-4-((TETRAHYDRO-2HPYRAN-4-YLMETHYL) AMINO)PHENYL)SULFONYL)-2-(1H-PYRROLO(2,3-B)PYRIDIN-5-YLOXY)BENZAMIDE": "VENETOCLAX",
        #     "ABT199": "VENETOCLAX",
        #     "ABT-199": "VENETOCLAX",
        #     "BENZAMIDE, 4-(4-((2-(4-CHLOROPHENYL)-4,4-DIMETHYL-1-CYCLOHEXEN-1-YL)METHYL)-1-PIPERAZINYL)-N-((3-NITRO-4-(((TETRAHYDRO-2H-PYRAN-4-YL)METHYL)AMINO)PHENYL)SULFONYL)-2-(1H-PYRROLO(2,3-B)PYRIDIN-5-YLOXY)-": "VENETOCLAX",
        #     "GDC-0199": "VENETOCLAX",
        #     "RG7601": "VENETOCLAX",
        #     "RG-7601": "VENETOCLAX",
        #     "VENCLEXTA": "VENETOCLAX",
        #     "VENCLYXTO": "VENETOCLAX",
        #     "VENETOCLAX": "VENETOCLAX",
        #     "VENETOCLAX [INN]": "VENETOCLAX",
        #     "VENETOCLAX [JAN]": "VENETOCLAX",
        #     "VENETOCLAX [MI]": "VENETOCLAX",
        #     "VENETOCLAX [ORANGE BOOK]": "VENETOCLAX",
        #     "VENETOCLAX [USAN]": "VENETOCLAX",
        #     "VENETOCLAX [WHO-DD]": "VENETOCLAX",
        # }

    def tearDown(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _create_temp_file(self, content, filename):
        """Helper to create a temporary file."""
        temp_file = Path(filename)
        with open(temp_file, "w") as f:
            f.write(content)
        self.temp_files.append(temp_file)
        return temp_file

    def test_standardization_from_dict(self):
        # Test standardizing a list of names
        input_names = [
            "ABT199",
            "VENCLEXTA",
            "VENETOCLAX [JAN]",
            "RG-7601",
            "GDC-0199",
        ]
        expected_output = ["VENETOCLAX"] * len(input_names)
        actual_output = [self.test_dict.get(name, name) for name in input_names]
        self.assertEqual(expected_output, actual_output)

    def test_json_input(self):
        # Simulate JSON input
        input_content = json.dumps(["ABT199", "RG7601", "VENCLYXTO", "GDC-0199"])
        input_file = self._create_temp_file(input_content, "test_input.json")
        output_file = "test_output.json"
        self.temp_files.append(output_file)

        standardize(
            input_data=str(input_file),
            output_file=output_file,
            file_type="json",
        )

        # Read and verify the output JSON file
        with open(output_file, "r") as f:
            output_data = json.load(f)

        expected_output = ["VENETOCLAX", "VENETOCLAX", "VENETOCLAX", "VENETOCLAX"]
        self.assertEqual(output_data, expected_output)

    def test_tsv_input(self):
        # Simulate TSV input
        input_tsv = "id,drug_name\n1,ABT199\n2,RG7601\n3,VENETOCLAX [WHO-DD]"
        input_file = self._create_temp_file(input_tsv, "test_input.tsv")
        output_file = "test_output.tsv"
        self.temp_files.append(output_file)

        standardize(
            input_data=str(input_file),
            output_file=output_file,
            file_type="tsv",
            column_drug=1,
            separator=",",
        )

        # Read and verify the output TSV file
        with open(output_file, "r") as f:
            output_data = f.read()

        expected_output = "id,drug_name\n1,VENETOCLAX\n2,VENETOCLAX\n3,VENETOCLAX\n"
        self.assertEqual(output_data.strip(), expected_output.strip())

    def test_unknown_drug_names(self):
        input_names = ["unknown_drug", "NON_EXISTENT", "FakeName"]
        expected_output = input_names  # Should return the same names if not found
        actual_output = standardize(input_names)
        self.assertEqual(expected_output, actual_output)

    def test_case_insensitivity(self):
        input_names = ["abt199", "rg7601", "VENCLEXTA"]
        expected_output = ["VENETOCLAX", "VENETOCLAX", "VENETOCLAX"]
        actual_output = standardize(input_names)
        self.assertEqual(expected_output, actual_output)

    def test_json_mixed_known_unknown(self):
        input_content = json.dumps(["ABT199", "UNKNOWN_DRUG", "RG7601", "uknDrug"])
        input_file = self._create_temp_file(input_content, "test_input_mixed.json")
        output_file = "test_output_mixed.json"
        self.temp_files.append(output_file)

        standardize(
            input_data=str(input_file),
            output_file=output_file,
            file_type="json",
        )

        with open(output_file, "r") as f:
            output_data = json.load(f)

        expected_output = ["VENETOCLAX", "UNKNOWN_DRUG", "VENETOCLAX", "uknDrug"]
        self.assertEqual(output_data, expected_output)

    def test_tsv_custom_separator(self):
        input_tsv = "id|drug_name\n1|ABT199\n2|RG7601\n3|VENETOCLAX [WHO-DD]"
        input_file = self._create_temp_file(input_tsv, "test_input_pipe.tsv")
        output_file = "test_output_pipe.tsv"
        self.temp_files.append(output_file)

        standardize(
            input_data=str(input_file),
            output_file=output_file,
            file_type="tsv",
            column_drug=1,
            separator="|",
        )

        with open(output_file, "r") as f:
            output_data = f.read()

        expected_output = "id|drug_name\n1|VENETOCLAX\n2|VENETOCLAX\n3|VENETOCLAX\n"
        self.assertEqual(output_data.strip(), expected_output.strip())

    def test_empty_input(self):
        # Empty list
        input_names = []
        expected_output = []
        actual_output = standardize(input_names, self.test_dict)
        self.assertEqual(expected_output, actual_output)

        # Empty JSON file
        input_content = json.dumps([])
        input_file = self._create_temp_file(input_content, "test_input_empty.json")
        output_file = "test_output_empty.json"
        self.temp_files.append(output_file)

        standardize(
            input_data=str(input_file),
            output_file=output_file,
            file_type="json",
        )

        with open(output_file, "r") as f:
            output_data = json.load(f)
        self.assertEqual(output_data, [])

    def test_resolve_ambiguities(self):
        ambiguous_dict = {
            "DRUG_A": ["DRUG_A_LONG_NAME", "DRUG_A"],
            "DRUG_B": ["DRUG_B_NAME", "DRUG_B_LONGER"],
            "DRUG_C": ["DRUG_C_NAME"]
        }
        unambiguous_dict = resolve_ambiguities(ambiguous_dict)
        expected_dict = {"DRUG_A": "DRUG_A", "DRUG_B": "DRUG_B_NAME", "DRUG_C": "DRUG_C_NAME"}
        self.assertEqual(unambiguous_dict, expected_dict)

    def test_invalid_unii_file_path(self):
        # Simulate an invalid path
        invalid_path = "non_existent_path/UNII_Names.txt"

        with self.assertRaises(FileNotFoundError) as context:
            standardize(
                input_data="ABT199",  # Example input data
                unii_file=invalid_path,  # Invalid path
            )

        # Verify the exception message
        self.assertIn("The UNII Names file you give as argument", str(context.exception))

    def test_broken_url(self):
        """
        Test handling of a broken or invalid URL for the FDA download.
        """
        with self.assertRaises(DownloadError) as context:
            download_unii_file(download_url="https://invalid-url-for-testing.com/UNIIs.zip")

        # Verify the error message includes the expected details
        self.assertIn("Failed to download the UNII file", str(context.exception))
        self.assertIn("invalid-url-for-testing.com", str(context.exception))


if __name__ == "__main__":
    unittest.main()
