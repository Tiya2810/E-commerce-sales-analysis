"""Shared project paths and settings."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = PROJECT_ROOT / "database"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"
SQL_DIR = PROJECT_ROOT / "sql"

RAW_DATA_PATH = DATA_DIR / "raw_data.csv"
CLEAN_DATA_PATH = DATA_DIR / "cleaned_data.csv"
DATABASE_PATH = DATABASE_DIR / "ecommerce.db"
RANDOM_SEED = 42

for directory in (DATA_DIR, DATABASE_DIR, ANALYSIS_DIR, CHARTS_DIR, SQL_DIR):
    directory.mkdir(parents=True, exist_ok=True)
