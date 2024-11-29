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

def convert2dataframe(input_string: str):
    # strip away the part of the line after a comment symbol '%'
    input_string = re.sub(r"%.*", "", input_string)
    # remove all the empty lines
    input_string = re.sub(r"\n\s*\n", "\n", input_string)
    # remove the leading and trailing whitespaces
    input_string = input_string.strip()
    # remove the \\ at the end of the line
    input_string = re.sub(r"\\\\", "", input_string)

    # split the table into rows
    rows = input_string.split("\n")
    # split each row into columns
    rows = [row.split("&") for row in rows]
    indices = [row[0] for row in rows]
    data = [row[1:] for row in rows]

    # Convert it into a DataFrame
    df = pd.DataFrame(data, index=indices)

    # Convert into numbers if possible
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(df[column])

    return df

def interacitve_highlighting():
    lines = read_input()
    table = convert2dataframe(lines)
    # Ask the user for the axis
    print("Please select the axis for highlighting:")
    print("0: Row")
    print("1: Column")
    axis = Axis(int(input("Enter the axis: ")))

    # Ask the user for the highlighting patterns as a comma-separated list of strings
    # Provide a default value as an example
    print("Please enter the highlighting patterns as a comma-separated list of strings:")
    print("Example: \\bfseries{%s},\\underline{%s}")
    print("If you want to use the default highlighting pattern, just press Enter")
    highlighting = (input("Enter the highlighting patterns: ") or "\\bfseries{%s},\\underline{%s}").split(",")

    # Ask the user for the default formatting pattern
    print("Please enter the default formatting pattern:")
    print("Example: %s")
    default = input("Enter the default formatting pattern: ") or "%s"

    if axis == Axis.ROW:
        table = table.T
    
    # for each column ask the user for the order and precision
    orders = []
    precisions = []
    for column in table.columns:
        print(f"Please select the order for column {column}:")
        print("-1: Minimum")
        print("0: Neural")
        print("1: Maximum")
        orders.append(Order(int(input("Enter the order: "))))
        print(f"Please enter the precision for column {column}:")
        print("Example: %.3f")
        print("If you want to use the default precision, just press Enter")
        precisions.append(input("Enter the precision: ") or "%.3f")


    rows, columns = table.shape
    ignore_idx = []
    remaining_indices = [idx for idx in range(rows) if idx not in ignore_idx]
    
    for idx, (column, order, precision) in enumerate(zip(table.columns, orders, precisions)):
        table[column] = column_highlighting(table[column], remaining_indices, order, highlighting, default, precision)
        
    if axis == Axis.ROW:
        table = table.T

    return table

