"""
Drugname Standardizer Package

This package is a tool for standardizing drug names using the FDA UNII Names List archive.
It allows standardization of individual names, lists, or file-based inputs (JSON, TSV).

Usage:
    from drugname_standardizer import DrugStandardizer

    ds = DrugStandardizer()
    print(ds.standardize_name("GDC-0199"))  # Output: VENETOCLAX
"""

__version__ = "1.2.6"
__author__ = "Stéphanie Chevalier"
__license__ = "MIT"
__release_date__ = "2025-06-12"

from .standardizer import DrugStandardizer
