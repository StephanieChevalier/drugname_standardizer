import json
import tempfile
from pathlib import Path

import pytest
from drugname_standardizer import DrugStandardizer

# -------------------------------
# Fixture unique pour initialiser l’objet
# -------------------------------
@pytest.fixture(scope="module")
def standardizer():
    return DrugStandardizer()

# -------------------------------
# Tests unitaires de la méthode standardize_name
# -------------------------------
def test_standardize_name_known(standardizer):
    # Hypothèse : "ACETAMINOPHEN" est dans le fichier UNII avec un nom court
    standardized = standardizer.standardize_name("acetaminophen")
    assert isinstance(standardized, str)
    assert standardized != "acetaminophen"
    assert standardized.isupper()

def test_standardize_name_unknown(standardizer):
    unknown_name = "NON_EXISTENT_DRUG"
    result = standardizer.standardize_name(unknown_name)
    assert result == unknown_name  # non trouvé → inchangé

# -------------------------------
# Test de standardisation d’une liste
# -------------------------------
def test_standardize_list_mixed(standardizer):
    drug_list = ["acetaminophen", "NON_EXISTENT_DRUG"]
    result = standardizer.standardize_list(drug_list)
    assert isinstance(result, list)
    assert result[0] != "acetaminophen"
    assert result[1] == "NON_EXISTENT_DRUG"

# -------------------------------
# Test de la méthode standardize_json_file
# -------------------------------
def test_standardize_json_file(standardizer):
    drugs = ["acetaminophen", "ibuprofen", "NON_EXISTENT_DRUG"]
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_input.json"
        output_path = Path(tmpdir) / "test_output.json"

        # Création du fichier JSON d’entrée
        with open(input_path, "w") as f:
            json.dump(drugs, f)

        # Appel de la méthode à tester
        standardizer.standardize_json_file(input_path, output_path)

        # Lecture du fichier JSON de sortie
        with open(output_path, "r") as f:
            output_data = json.load(f)

        assert isinstance(output_data, list)
        assert len(output_data) == 3
        assert output_data[0].isupper()
        assert output_data[2] == "NON_EXISTENT_DRUG"

# -------------------------------
# Test CLI (exécution subprocess) – optionnel mais recommandé
# -------------------------------
import subprocess

def test_cli_simple_call():
    result = subprocess.run(
        ["drugname_standardizer", "-i", "acetaminophen"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip().isupper()

# -------------------------------
# Test : liste vide
# -------------------------------
def test_standardize_list_empty(standardizer):
    result = standardizer.standardize_list([])
    assert result == []

# -------------------------------
# Test : séparateur personnalisé pour TSV
# -------------------------------
def test_standardize_tsv_custom_separator(standardizer):
    import csv

    rows = [
        ["id", "drug"],
        ["1", "ABT199"],
        ["2", "GDC-0199"],
        ["3", "VENCLYXTO"]
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.tsv"
        output_path = Path(tmpdir) / "output.tsv"

        with open(input_path, "w", newline="") as f:
            writer = csv.writer(f, delimiter="|")
            writer.writerows(rows)

        standardizer.standardize_tsv_file(
            input_path=input_path,
            output_path=output_path,
            column_drug=1,
            separator="|"
        )

        with open(output_path, "r") as f:
            lines = f.readlines()
            assert "VENETOCLAX" in lines[1]
            assert "VENETOCLAX" in lines[2]
            assert "VENETOCLAX" in lines[3]
