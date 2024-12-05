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


    data_lines = []
    multirow_counters = {}
    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip LaTeX table environment lines and \toprule, \bottomrule, \hline, \cmidrule
        if re.match(r'\\begin\{tabular\}', line) or re.match(r'\\end\{tabular\}', line):
            continue
        if re.match(r'\\(top|bottom|mid)rule', line):
            continue
        if re.match(r'\\hline', line):
            continue
        if re.match(r'\\cmidrule', line):
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

        # account for \multicolumn
        final_cells = []
        for cell in cells:
            multicol_match = re.match(r'\\multicolumn\{(\d+)\}\{[^\}]*\}\{(.+)\}', cell)
            if multicol_match:
                span = int(multicol_match.group(1))
                content = multicol_match.group(2).strip()
                final_cells.extend([content] * span)
            else:
                final_cells.append(cell)

        # add multirow from previous line
        for col, (count, content) in multirow_counters.items():
            if count > 0:
                final_cells[col] = content
                multirow_counters[col] = (count - 1, content)
            
        # pop multirow counters that are 0
        multirow_counters = {col: (count, content) for col, (count, content) in multirow_counters.items() if count > 0}

        # check for multirow command and add to the counter
        for idx, cell in enumerate(final_cells):
            multirow_match = re.match(r'\\multirow\{(\d+)\}\{[^\}]*\}\{(.+)\}', cell)
            if multirow_match:
                span = int(multirow_match.group(1))
                content = multirow_match.group(2).strip()
                multirow_counters[idx] = (span - 1, content)
                final_cells[idx] = content

        data_lines.append(final_cells)

    # Create DataFrame
    df = pd.DataFrame(data_lines)

    # Function to extract numerical value from a cell
    def extract_number(cell):
        if cell == "":
            return cell
        # Remove LaTeX commands like \underline{} from around numbers
        cell_wo_commands = re.sub(r'\\[a-zA-Z]+\{([^}]+)\}', r'\1', cell)
        cell_wo_commands = cell_wo_commands.strip()
        # if only a number is left, turn it into a float
        if re.match(r'-?\d+\.?\d*', cell_wo_commands):
            return float(cell_wo_commands)
        return cell
    
    # Apply the extraction function to all cells
    df = df.applymap(extract_number)

    # Figure out which rows are headers and which columns are indices by checking where there are numbers
    header_indices = []
    for idx, row in df.iterrows():
        if any(isinstance(cell, float) for cell in row):
            break
        header_indices.append(idx)
    index_indices = []
    for idx, col in enumerate(df):
        column = df[col]
        if any(isinstance(cell, float) for cell in column):
            break
        index_indices.append(idx)

    # extract the headers and indices
    non_index_columns = [idx for idx in range(len(df.columns)) if idx not in index_indices]
    non_header_rows = [idx for idx in range(len(df)) if idx not in header_indices]
    headers = df.iloc[header_indices, non_index_columns]
    indices = df.iloc[non_header_rows, index_indices]
    data = df.iloc[non_header_rows, non_index_columns]

    return pd.DataFrame(data.values, index=indices.T.values.tolist(), columns=headers.values.tolist())
