# pandas2latex

pandas2latex is a terminal-based application that allows users to input tabular data, manipulate it, apply custom highlighting rules, and prepare it for LaTeX export. The application is built using Python and leverages the `textual` library to provide a rich, interactive text-based user interface.

## Features

- **Data Input**: Easily input data into the application using plain text, which is then converted into a pandas DataFrame.
- **Data Display**: View your data in a tabular format within the terminal.
- **Custom Highlighting**: Define default and column-specific highlighting rules to emphasize important data.
- **Column Manipulation**: Swap columns and toggle their order to customize the data presentation.
- **Interactive Interface**: Navigate and interact with your data using keyboard shortcuts.

## Installation

Ensure you have Python 3.10 or higher installed. Install the project dependencies using pip:

```bash
pip install .
```

## Usage

Run the application from the command line:

```bash
python src/p2l_ui2.py
```

## Keyboard Shortcuts

- `N`: Open the input screen to enter new data.
- `d`: Edit the default highlighting rules.
- `c`: Edit column-specific highlighting rules.
- `S`: Start the column swap mode.
- `s`: Select a column for swapping (used in swap mode).
- `Enter`: Submit highlighting rules.
- `Ctrl+S`: Submit input data or highlighting rules in input screens.

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
   - Submit the rules by pressing `Ctrl+S`.
   - The table updates to reflect the new highlighting, emphasizing important data points based on the rules provided.

4. **Manipulating Columns**:
   - Activate swap mode by pressing `S`.
   - Select columns to swap by navigating to them and pressing `s`.
   - Swap selected columns to reorganize the data layout.
   - Toggle column order (minimum, neutral, maximum) by selecting a column header.

5. **Preparing for LaTeX Export**:
   - After making all desired modifications, the application formats the data for LaTeX export.
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