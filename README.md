# latex-table-editor

latex-table-editor is a terminal-based application that allows users to input tabular data, manipulate it, apply custom highlighting rules, and prepare it for LaTeX export. The application is built using Python and leverages the `textual` library to provide a rich, interactive text-based user interface.

## Features

- **Data Input**: Easily input data into the application using plain text, which is then converted into a pandas DataFrame.
- **Data Display**: View your data in a tabular format within the terminal.
- **Custom Highlighting**: Define default and column-specific highlighting rules to emphasize important data.
- **Column Manipulation**: Swap columns and toggle their order to customize the data presentation.
- **Interactive Interface**: Navigate and interact with your data using keyboard shortcuts.
- **Enhanced Table Parsing**: Supports `multicolumn` and `multirow` LaTeX commands, allowing complex table structures to be parsed accurately. Data cells are automatically inferred from the table structure.
- **Dynamic Sorting Properties**: Quickly change sorting order and precision using new keyboard shortcuts.
- **Selective Data Exclusion**: Exclude rows in column mode and columns in row mode from computations of extreme values for more tailored data analysis.

## Installation

Ensure you have Python 3.10 or higher installed. Install the project dependencies using pip:

```bash
pip install git+https://github.com/DominikMuhle/latex-table-editor.git
```

## Usage

Run the application from the command line:

```bash
lte
```

## Keyboard Shortcuts

- `N`: Open the input screen to enter new data.
- `d`: Edit the default highlighting rules.
- `c`: Edit column-specific highlighting rules.
- `S`: Start the column swap mode.
- `s`: Select a column for swapping (used in swap mode).
- `Enter`: Submit highlighting rules.
- `Ctrl+S`: Submit input data or highlighting rules in input screens.
- `+`: Increase precision of the selected column or row.
- `-`: Decrease precision of the selected column or row.
- `o`: Toggle sorting order of the selected column or row (minimum, neutral, maximum).
- `x`: Exclude/include the selected column or row from computations.
- `e`: Edit highlighting rules for the selected column or row.

## How It Works

When the application starts, users can interact with their data through a series of intuitive screens and commands:

1. **Entering Data**:
   - Press `N` to open the input screen.
   - Input tabular data in plain text format.
   - Submit the data by pressing `Ctrl+S`.
   - The data is converted into a pandas DataFrame and displayed in a table within the terminal.

2. **Viewing and Navigating Data**:
   - Use arrow keys to navigate through the data table.
   - The table provides an interactive view of the data for easy examination.

3. **Customizing Highlighting**:
   - Press `d` to edit default highlighting rules that apply to all columns.
   - Press `c` to edit column-specific highlighting rules.
   - Input the highlighting rules in JSON format.
   - **Adjust Sorting Properties**:
     - Press `+` or `-` to increase or decrease the precision for the selected column or row.
     - Press `o` to toggle the sorting order among minimum, neutral, and maximum.
     - Press `x` to exclude or include the selected column or row from extreme value computations.
   - Submit the rules by pressing `Ctrl+S`.
   - The table updates to reflect the new highlighting, emphasizing important data points based on the rules provided.

4. **Manipulating Data**:
   - **Toggle Mode**:
     - Press `T` to toggle between column mode and row mode.
     - In column mode, you can manipulate columns; in row mode, you can manipulate rows.
   - **Swapping Columns or Rows**:
     - Activate swap mode by pressing `S`.
     - Select columns or rows to swap by navigating to them and pressing `s`.
     - Swap selected columns or rows to reorganize the data layout.
   - **Toggling Order**:
     - Toggle column or row order (minimum, neutral, maximum) by selecting a column or row header.

5. **Preparing for LaTeX Export**:
   - After making all desired modifications, the application formats the data for LaTeX export.
   - The application now supports LaTeX tables with `multicolumn` and `multirow` commands.
   - Data cells are automatically inferred from the table structure, ensuring accurate data representation.
   - The final output includes all customizations, ready to be integrated into LaTeX documents.

## Custom Highlighting

Highlighting rules can be customized using JSON input. The rules can specify ordering and other formatting options to highlight data based on minimum, maximum, or neutral values.

Example default highlighting rule:

```json
{
    "order": "max",
    "highlighting": [
        "\\bfseries{%s}",
        "\\underline{%s}",
    ],
    "default": "%s",
    "precision": "%.2f",
}
```

This rule will highlight the largest value in **bold** and <u>underlined</u>, while other values will be displayed normally. The precision is set to two decimal places.

## Column Manipulation

- **Swap Mode**: Activate swap mode by pressing `S`. Select two columns by pressing `s` on each, and the columns will be swapped.
- **Toggle Column Order**: Click on a column header or press the corresponding key to toggle its order among minimum, neutral, and maximum.

## Dependencies

- Python >= 3.10
- pandas >= 2.2.3
- jinja2 >= 3.1.4
- textual >= 0.87.1
- pytest >= 8.3.3 (for running tests)

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss any changes or suggestions.

## License

[MIT License](LICENSE)
