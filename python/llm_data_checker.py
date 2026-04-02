########################
#Libraries
########################

import sys

import pandas as pd
import pathlib 
import numpy as np
from scipy.stats import entropy

########################
#Data Read in function 
########################

#This function was written by me 
def read_df(input):
    if isinstance(input, pd.DataFrame):
        return input
    
    try:
        path = pathlib.Path(input)

    except TypeError:
        raise TypeError("Input must be a DataFrame or a path to a CSV file")

    if path.is_file() and path.suffix == ".csv":
        return pd.read_csv(path)


    print("Error. Try pass a CSV direct or Filepath to a CSV.", file=sys.stderr)
    return None



########################
#Main function to call
########################

# For the sake of transparency, this function was created by ChatGPT and was derived from the original df_checker function, 
# but with significant enhancements to provide context around structural characteristics of the data while preserving privacy. 

def get_structure_pattern(val):
    """
    Extract structural characteristics without exposing content.
    
    This reveals FORMAT issues without revealing DATA.
    """
    if pd.isna(val):
        return None
    
    val_str = str(val)
    
    # Create a structure representation
    structure = []
    i = 0
    while i < len(val_str):
        char = val_str[i]
        if char.isalpha():
            # Count consecutive letters
            count = 1
            while i + count < len(val_str) and val_str[i + count].isalpha():
                count += 1
            structure.append(f"ALPHA({count})")
            i += count
        elif char.isdigit():
            # Count consecutive digits
            count = 1
            while i + count < len(val_str) and val_str[i + count].isdigit():
                count += 1
            structure.append(f"DIGIT({count})")
            i += count
        elif char in ['\n', '\t', '\r']:
            structure.append(f"NEWLINE" if char == '\n' else "TAB" if char == '\t' else "RETURN")
            i += 1
        elif char == ' ':
            structure.append("SPACE")
            i += 1
        else:
            structure.append(f"'{char}'")
            i += 1
    
    return '-'.join(structure[:20])  # Limit length



# For the sake of transparency, this function was created by ChatGPT based on the original df_checker function, but with significant enhancements to provide
# more structural insights while preserving privacy. The original function is still available upon request for comparison, 
# but this new version (df_checker_v2) is designed to be more robust and informative without exposing any actual data content.
def df_checker_v2(data: pd.DataFrame) -> dict:
    """
    Enhanced privacy-preserving structural data analysis.

    This version introduces:
    - Entropy scoring
    - Unique ratio detection
    - Identifier likelihood detection
    - Mixed-type detection
    - Skewness
    - Outlier percentage
    - Near-zero variance detection

    All outputs avoid exposing actual content.
    """

    # ==============================
    # BASIC DATASET METRICS
    # ==============================

    # Extract number of rows and columns
    shape = data.shape  # tuple (rows, columns)

    # Extract column names (structure only, no data)
    col_names = data.columns.tolist()

    # Count data types present in dataset
    dtype_counts = {str(k): int(v) for k, v in data.dtypes.value_counts().items()}

    # Identify numeric columns using pandas dtype inference
    numeric_cols = data.select_dtypes(include="number").columns.tolist()

    # Identify object (categorical/string) columns
    cat_cols = data.select_dtypes(include="object").columns.tolist()

    # ==============================
    # MISSING VALUE ANALYSIS
    # ==============================

    # Compute percentage of missing values per column
    per_null = data.isna().mean() * 100

    # Extract only columns with >10% missing
    cols_high_missing = per_null[per_null > 10].round(2).to_dict()

    # ==============================
    # COLUMN SUMMARIES
    # ==============================

    column_profiles = {}

    for col in data.columns:

        series = data[col]

        # Drop NA values for structural analysis
        non_null = series.dropna()

        total_rows = len(series)

        if total_rows == 0:
            continue

        # ----------------------------------
        # UNIQUENESS ANALYSIS
        # ----------------------------------

        # Count unique values
        nunique = series.nunique(dropna=True)

        # Ratio of unique values to total rows
        unique_ratio = nunique / total_rows

        # ----------------------------------
        # ENTROPY (ID / randomness detection)
        # ----------------------------------

        entropy_score = None
        if 1 < nunique < 10000:
            # Normalized frequency distribution
            probs = non_null.value_counts(normalize=True)

            # Shannon entropy
            entropy_score = float(entropy(probs, base=2))

        # ----------------------------------
        # DOMINANT VALUE (variance signal)
        # ----------------------------------

        dominant_pct = None
        near_zero_variance = False

        if nunique > 0:
            dominant_pct = float(non_null.value_counts(normalize=True).iloc[0] * 100)
            near_zero_variance = dominant_pct > 95

        # ----------------------------------
        # TYPE-SPECIFIC ANALYSIS
        # ----------------------------------

        profile = {
            "unique_count": int(nunique),
            "unique_ratio": round(unique_ratio, 3),
            "entropy": round(entropy_score, 2) if entropy_score else None,
            "dominant_value_pct": round(dominant_pct, 1) if dominant_pct else None,
            "near_zero_variance": near_zero_variance,
        }

        # ----------------------------------
        # NUMERIC COLUMN ANALYSIS
        # ----------------------------------

        if col in numeric_cols and len(non_null) > 0:

            # Basic descriptive statistics
            mean = float(non_null.mean())
            std = float(non_null.std())
            min_val = float(non_null.min())
            max_val = float(non_null.max())

            # Skewness detection
            skewness = float(non_null.skew())

            # IQR-based outlier detection
            if len(non_null) > 20:
                q1 = non_null.quantile(0.25)
                q3 = non_null.quantile(0.75)
                iqr = q3 - q1

                outliers = ((non_null < q1 - 1.5 * iqr) |
                            (non_null > q3 + 1.5 * iqr)).sum()

                outlier_pct = outliers / total_rows * 100
            else:
                outlier_pct = None

            profile.update({
                "mean": round(mean, 2),
                "std": round(std, 2),
                "min": min_val,
                "max": max_val,
                "skewness": round(skewness, 2),
                "highly_skewed": abs(skewness) > 2,
                "outlier_pct": round(outlier_pct, 2) if outlier_pct else None,
            })

        # ----------------------------------
        # CATEGORICAL COLUMN ANALYSIS
        # ----------------------------------

        if col in cat_cols and len(non_null) > 0:

            # Convert values to string
            str_vals = non_null.astype(str)

            # Detect numeric-like strings
            numeric_like_ratio = str_vals.str.match(
                r'^-?\d+(\.\d+)?$'
            ).mean()

            mixed_type = 0.2 < numeric_like_ratio < 0.8

            profile.update({
                "numeric_like_ratio": round(float(numeric_like_ratio), 3),
                "mixed_type_suspected": mixed_type,
            })

        # ----------------------------------
        # IDENTIFIER LIKELIHOOD FLAG
        # ----------------------------------

        likely_identifier = (
            unique_ratio > 0.95 and
            entropy_score is not None and
            entropy_score > 4
        )

        profile["likely_identifier"] = likely_identifier

        column_profiles[col] = profile

        # ==============================
        # COLUMN NAME STRUCTURAL ANALYSIS
        # ==============================

        column_name_profiles = {}

        for col in data.columns:

            name = str(col)

            # Basic structural properties
            length = len(name)
            contains_digit = any(c.isdigit() for c in name)
            contains_special = any(not c.isalnum() and c != "_" for c in name)

            # Tokenisation by underscore and basic camelCase splitting
            tokens = (
                name.replace("-", "_")
                    .replace(" ", "_")
                    .split("_")
            )

            token_count = len([t for t in tokens if t])

            # Case pattern detection
            if name.isupper():
                case_type = "UPPERCASE"
            elif name.islower():
                case_type = "lowercase"
            elif "_" in name:
                case_type = "snake_case"
            elif name[:1].isupper() and not "_" in name:
                case_type = "PascalCase"
            elif any(c.isupper() for c in name[1:]):
                case_type = "camelCase"
            else:
                case_type = "mixed"

            # Semantic keyword detection (non-sensitive heuristics)
            lowered = name.lower()

            semantic_flags = {
                "likely_id_column": any(k in lowered for k in ["id", "uuid", "key", "ref"]),
                "likely_datetime_column": any(k in lowered for k in ["date", "time", "timestamp"]),
                "likely_amount_column": any(k in lowered for k in ["amount", "price", "cost", "revenue", "salary"]),
                "likely_count_column": any(k in lowered for k in ["count", "num", "qty", "quantity"]),
                "likely_ratio_column": any(k in lowered for k in ["rate", "pct", "percent", "ratio"]),
            }

            column_name_profiles[name] = {
                "length": length,
                "token_count": token_count,
                "contains_digit": contains_digit,
                "contains_special_char": contains_special,
                "case_pattern": case_type,
                **semantic_flags
            }
    return {
        "shape": shape,
        "dtype_counts": dtype_counts,
        "high_missing_columns_pct": cols_high_missing,
        "column_profiles": column_profiles,
        "column_name_profiles": column_name_profiles,
        "privacy_note": "All metrics derived from structural and schema-level properties only."
    }
