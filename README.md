# latex-table-editor

latex-table-editor is a terminal-based application that allows users to input tabular data in various formats, manipulate it, apply custom highlighting rules, and prepare it for LaTeX export. The application is built using Python and leverages the `textual` library to provide a rich, interactive text-based user interface.

## Features

- **Data Input**: Input data in LaTeX, plain text, JSON, YAML, or CSV formats.
- **Data Display**: View your data in a tabular format within the terminal.
- **Custom Highlighting**: Define highlighting rules using an interactive screen with enforced input validation.
- **Column and Row Manipulation**: Swap columns or rows, toggle their order, and adjust data selection.
- **Interactive Interface**: Navigate and interact with your data using keyboard shortcuts.
- **Adjustable Data Selection**: Correct the selection of data parts of the table through a dedicated screen.
- **LaTeX Export**: Prepare your data with all customizations for LaTeX export, including support for `multicolumn` and `multirow`.

## Installation

Ensure you have Python 3.10 or higher installed. Install the project using pip:

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
- `L`: Show the LaTeX output screen.
- `T`: Toggle between column mode and row mode.
- `R`: Edit highlighting rules in a dedicated screen.
- `S`: Start selection mode to swap columns or rows.
- `s`: Select a column or row for swapping (used in selection mode).
- `t`: Adjust headers and indices in the data selection screen.
- `+`: Increase precision of the selected column or row.
- `-`: Decrease precision of the selected column or row.
- `o`: Toggle sorting order of the selected column or row (minimum, neutral, maximum).
- `x`: Exclude/include the selected column or row from computations.

## How It Works

When the application starts, users can interact with their data through a series of intuitive screens and commands:

1. **Entering Data**:
   - Press `N` to open the input screen.
   - Select the input format (LaTeX, String, JSON, YAML, CSV).
   - Input your data in the chosen format.
   - Submit the data by pressing `Ctrl+S`.
   - The data is converted into a pandas DataFrame and displayed in a table within the terminal.

2. **Viewing and Navigating Data**:
   - Use arrow keys to navigate through the data table.
   - The table provides an interactive view of the data for easy examination.

3. **Customizing Highlighting Rules**:
   - Press `R` to edit highlighting rules in a dedicated screen presented in a DataTable format.
   - Input validation ensures correct formats for rules.

4. **Manipulating Data**:
   - **Toggle Mode**:
     - Press `T` to toggle between column mode and row mode.
     - In column mode, manipulate columns; in row mode, manipulate rows.
   - **Swapping Columns or Rows**:
     - Activate selection mode by pressing `S`.
     - Select columns or rows to swap by navigating to them and pressing `s`.
     - Swap selected items to reorganize the data layout.
   - **Adjusting Data Selection**:
     - Press `t` to open a screen to adjust headers and indices, correcting the selection of the data part of the table.

5. **Preparing for LaTeX Export**:
   - After making all desired modifications, the application formats the data for LaTeX export.
   - Data cells are automatically inferred from the table structure, ensuring accurate data representation.
   - The final output includes all customizations, ready to be integrated into LaTeX documents.

## Custom Highlighting

Highlighting rules can be customized through an interactive screen that enforces correct input formats. Rules specify ordering and formatting options to highlight data based on minimum, maximum, or neutral values.

## Dependencies

- Python >= 3.10
- pandas >= 2.2.3
- jinja2 >= 3.1.4
- textual >= 0.87.1
- pytest >= 8.3.3 (for running tests)

## Development

### Setting up the Python environment

Install `uv` using pip:

```bash
pip install uv
```

Set up the Python environment from the `pyproject.toml` file:

```bash
uv sync
```

Activate the environment:

```bash
source .venv/bin/activate
```

### Running the tests

To run the tests, use the following command:

```bash
pytest
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss any changes or suggestions.

## License

[MIT License](LICENSE)
