import re

import pandas as pd

from highlighting import column_highlighting
from utils import Axis, Order


def read_input():
    print("Please input your table via copy and paste. Press Ctrl-D on Linux/Max when you are done. Press Ctrl-Z on Windows when you are done.")
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass
    return "\n".join(lines)


def latex_table_to_dataframe(latex_str: str) -> pd.DataFrame:
    """
    Convert LaTeX table source code into a pandas DataFrame.

    Parameters:
    - latex_str (str): LaTeX table as a string.

    Returns:
    - pd.DataFrame: DataFrame representation of the LaTeX table.
    """
    # Split the LaTeX string into individual lines
    lines = latex_str.strip().splitlines()

    rows = []
    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip LaTeX table environment lines
        if re.match(r'\\begin\{tabular\}', line) or re.match(r'\\end\{tabular\}', line):
            continue

        # Skip table rules like \toprule, \midrule, \bottomrule
        if re.match(r'\\(top|mid|bottom)rule', line):
            continue

        # Remove comments starting with %
        line = re.sub(r'%.*', '', line).strip()
        if not line:
            continue

        # Remove trailing '\\'
        line = re.sub(r'\\\\', '', line).strip()
        if not line:
            continue

        # Split the line by '&' and strip whitespace from each cell
        cells = [cell.strip() for cell in line.split('&')]
        rows.append(cells)

    if not rows:
        return pd.DataFrame()

    # Assume the first row is the header
    header = rows[0]
    data_rows = rows[1:]

    if not data_rows:
        # If there's no data, return empty DataFrame with headers
        return pd.DataFrame(columns=header[1:], index=[])

    # Use the first column as the index
    index = [row[0] for row in data_rows]
    data = [row[1:] for row in data_rows]

    # Create DataFrame
    df = pd.DataFrame(data, index=index, columns=header[1:])

    # Function to extract numerical value from a cell
    def extract_number(cell):
        # Remove LaTeX commands like \underline{}
        cell = re.sub(r'\\[a-zA-Z]+\{([^}]+)\}', r'\1', cell)
        cell = cell.strip()
        # Check for non-numeric entries like '-'
        if cell == '-':
            return cell
        # Extract numerical value
        match = re.search(r'-?\d+\.?\d*', cell)
        return float(match.group()) if match else cell

    # Apply the extraction function to all cells
    df = df.applymap(extract_number)

    return df
