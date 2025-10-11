import pandas as pd
from pathlib import Path
import json

def extract_table_data(filepath: Path) -> list[dict]:
    """
    Extracts structured data and metadata from CSV or Excel files.

    For Excel files, each sheet is treated as a separate table.

    Args:
        filepath: Path to the file.

    Returns:
        A list of dictionaries, where each dictionary contains the
        metadata for one table (or sheet). Returns an empty list if
        the file cannot be processed.
    """
    file_extension = filepath.suffix.lower()
    results = []

    try:
        if file_extension == '.csv':
            # For CSVs, treat the file itself as a single sheet.
            df = pd.read_csv(filepath, on_bad_lines='skip')
            sheet_name = filepath.stem
            results.append(profile_dataframe(df, sheet_name))

        elif file_extension in ['.xlsx', '.xls']:
            # For Excel, iterate through each sheet.
            xls = pd.ExcelFile(filepath)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                results.append(profile_dataframe(df, sheet_name))

    except Exception as e:
        print(f"Error processing table file {filepath}: {e}")
        return []

    return results

def profile_dataframe(df: pd.DataFrame, sheet_name: str) -> dict:
    """
    Generates a profile for a single pandas DataFrame.
    """
    n_rows, n_cols = df.shape

    # Handle empty dataframes
    if n_rows == 0:
        return {
            "sheet_name": sheet_name,
            "n_rows": 0,
            "n_cols": n_cols,
            "columns": list(df.columns),
            "profile_json": "{}",
            "exemplars_json": "[]"
        }

    # Generate column profiles
    column_profiles = {}
    for col in df.columns:
        # Ensure column name is a string
        col_name = str(col)
        col_series = df[col]
        dtype = str(col_series.dtype)

        # Profile numeric columns
        if pd.api.types.is_numeric_dtype(col_series):
            stats = col_series.describe().to_dict()
            # Ensure stats are JSON serializable (e.g., handle NaN)
            cleaned_stats = {k: (None if pd.isna(v) else v) for k, v in stats.items()}
            column_profiles[col_name] = {
                "dtype": dtype,
                "stats": cleaned_stats
            }
        # Profile categorical/object columns
        else:
            # Convert all values to string to avoid errors with mixed types
            value_counts = col_series.astype(str).value_counts().nlargest(10)
            column_profiles[col_name] = {
                "dtype": dtype,
                "num_unique": col_series.nunique(),
                "value_counts": value_counts.to_dict()
            }

    # Extract exemplars (first 5 rows)
    exemplars = df.head(5).to_dict(orient='records')
    # Ensure exemplars are JSON serializable
    cleaned_exemplars = [
        {str(k): (None if pd.isna(v) else v) for k, v in row.items()}
        for row in exemplars
    ]

    return {
        "sheet_name": sheet_name,
        "n_rows": n_rows,
        "n_cols": n_cols,
        "profile_json": json.dumps(column_profiles, default=str),
        "exemplars_json": json.dumps(cleaned_exemplars, default=str)
    }