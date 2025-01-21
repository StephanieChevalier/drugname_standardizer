"""
Drugname Standardizer Package

This package is a tool for standardizing drug names based on the FDA's UNII
Names List archive. It supports to directly standardize from JSON and TSV.

Modules:
- standardizer: Core functions for parsing the UNII file, resolving ambiguities,
  and standardizing drug names in files.

Usage:
    from drugname_standardizer import standardize

Release Date: January 16, 2025
"""

__version__ = "1.2.1"
__author__ = "Stéphanie Chevalier"
__license__ = "MIT"
__release_date__ = "2025-01-16"

from .standardizer import parse_unii_file, standardize, main
