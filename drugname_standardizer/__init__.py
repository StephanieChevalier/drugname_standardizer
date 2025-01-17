"""
Drugname Standardizer Package

This package is a tool for standardizing drug names based on the FDA UNII Names 
List archive. It supports both JSON and CSV input/output formats.

Modules:
- standardizer: Core functions for parsing the UNII file, resolving ambiguities,
  and standardizing drug names in files.

Usage:
    from drugname_standardizer import standardize_drug_names

Release Date: January 16, 2025C
"""

__version__ = "1.0.0"
__author__ = "Stéphanie Chevalier"
__license__ = "MIT"
__release_date__ = "2025-01-16"

from .standardizer import parse_unii_file, standardize_drug_names
