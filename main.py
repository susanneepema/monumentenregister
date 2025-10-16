import pandas as pd
import geopandas as gpd
import os
from datetime import datetime


def load_data(filepath: str):
    """
    Load either Excel or GeoPackage into a pandas DataFrame.
    Detects file type based on extension.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext in [".xlsx", ".xls"]:
        df = pd.read_excel(filepath)
    elif ext == ".gpkg":
        df = gpd.read_file(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return df


def compare_columns(file1, col1, file2, col2,
                    target_file="file2",
                    log_path="comparison_log.txt",
                    output_path="comparison_results.csv"):
    """
    Compare two datasets (Excel or GPKG) based on the specified columns.
    - Only considers values with exactly 16 digits.
    - Prints and logs:
        * how many and which values were ignored,
        * values only in one file,
        * values occurring in both.
    """
    # Load both
    df1 = load_data(file1)
    df2 = load_data(file2)

    # Check if columns exist
    if col1 not in df1.columns:
        raise ValueError(f"Column '{col1}' not found in {file1}")
    if col2 not in df2.columns:
        raise ValueError(f"Column '{col2}' not found in {file2}")

    # Convert to string
    df1[col1] = df1[col1].astype(str)
    df2[col2] = df2[col2].astype(str)

    # Filter valid 16-digit numeric values
    valid_mask1 = df1[col1].str.match(r'^\d{16}$', na=False)
    valid_mask2 = df2[col2].str.match(r'^\d{16}$', na=False)

    df1_valid = df1[valid_mask1]
    df2_valid = df2[valid_mask2]
    ignored1 = df1.loc[~valid_mask1, col1].unique().tolist()
    ignored2 = df2.loc[~valid_mask2, col2].unique().tolist()

    # Convert to sets
    set1 = set(df1_valid[col1])
    set2 = set(df2_valid[col2])

    # Compare
    only_in_file1 = sorted(set1 - set2)
    only_in_file2 = sorted(set2 - set1)
    in_both = sorted(set1 & set2)

    # Print to console
    print(f"\n📊 Comparison results (only 16-digit values considered):")
    print(f"- {os.path.basename(file1)}: {len(df1_valid)} valid, {len(ignored1)} ignored")
    print(f"- {os.path.basename(file2)}: {len(df2_valid)} valid, {len(ignored2)} ignored")
    print(f"- {len(only_in_file1)} values only in {os.path.basename(file1)}")
    print(f"- {len(only_in_file2)} values only in {os.path.basename(file2)}")
    print(f"- {len(in_both)} values occur in both\n")

    # Write log file
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"Comparison log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 70 + "\n\n")
        log.write(f"File 1: {file1}\nColumn: {col1}\n")
        log.write(f"File 2: {file2}\nColumn: {col2}\n\n")

        log.write(f"--- Ignored values (not 16 digits) ---\n")
        log.write(f"\nIgnored in {os.path.basename(file1)} ({len(ignored1)}):\n")
        for v in ignored1:
            log.write(f"   {v}\n")

        log.write(f"\nIgnored in {os.path.basename(file2)} ({len(ignored2)}):\n")
        for v in ignored2:
            log.write(f"   {v}\n")

        log.write("\n--- Values only in first file ---\n")
        for v in only_in_file1:
            log.write(f"   {v}\n")

        log.write("\n--- Values only in second file ---\n")
        for v in only_in_file2:
            log.write(f"   {v}\n")

        log.write("\n--- Values in both files ---\n")
        for v in in_both:
            log.write(f"   {v}\n")

    print(f"📝 Log file saved to: {os.path.abspath(log_path)}")

    # --- RESULT FILE ---
    if target_file == "file1":
        target_name = os.path.basename(file1)
        only_in_target = only_in_file1
        id_col = col1
    elif target_file == "file2":
        target_name = os.path.basename(file2)
        only_in_target = only_in_file2
        id_col = col2
    else:
        raise ValueError("target_file must be 'file1' or 'file2'")

    # Build dataframe for output
    results = pd.DataFrame({id_col: in_both + only_in_target})
    results["status"] = ["occur_both"] * len(in_both) + [f"occur_in_{target_file}"] * len(only_in_target)

    # Save
    results.to_csv(output_path, index=False)
    print(f"✅ Results written to: {os.path.abspath(output_path)}")
    print(f"Included: {len(results)} rows (occur_both + occur_in_one in {target_name})")

    return {
        "only_in_file1": only_in_file1,
        "only_in_file2": only_in_file2,
        "in_both": in_both,
        "ignored_in_file1": ignored1,
        "ignored_in_file2": ignored2
    }




# Example usage
if __name__ == "__main__":
    results = compare_columns(
        file1="input/monumenten.gpkg",
        col1="imgeo_identificatiebag",
        file2="input/monumentenbestand.xlsx",
        col2="BAG_ID_Pand",
        log_path="comparison_log.txt",
        output_path="comparison_results.csv"
    )

    # If you want to inspect the overlapping values:
    print("\nShared values example (up to 10):", list(results['in_both'])[:10])
