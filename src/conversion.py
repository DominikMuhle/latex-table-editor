import re

import pandas as pd

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

    # Initialize variables to store headers and data rows
    header_rows = []
    data_rows = []
    in_header = True

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip LaTeX table environment lines and \toprule, \bottomrule
        if re.match(r'\\begin\{tabular\}', line) or re.match(r'\\end\{tabular\}', line):
            continue
        if re.match(r'\\(top|bottom)rule', line):
            continue

        # Detect \midrule to signal the end of headers
        if re.match(r'\\midrule', line):
            in_header = False
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

        if in_header:
            header_cells = []
            for cell in cells:
                # Handle \multicolumn in header cells
                multicol_match = re.match(r'\\multicolumn\{(\d+)\}\{[^\}]*\}\{(.+)\}', cell)
                if multicol_match:
                    span = int(multicol_match.group(1))
                    content = multicol_match.group(2).strip()
                    header_cells.extend([content] * span)
                else:
                    header_cells.append(cell)
            header_rows.append(header_cells)
        else:
            data_rows.append(cells)

    # Extract columns, rows, and headers
    columns = [header_row[1:] for header_row in header_rows]
    index = [row[0] for row in data_rows]
    data = [row[1:] for row in data_rows]

    # Create DataFrame
    df = pd.DataFrame(data, index=index, columns=columns)

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
