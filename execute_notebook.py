"""Execute all notebook cells in-process, including rich outputs, without sockets."""
from pathlib import Path
import os
import time
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    path = root / "Extreme_Weather_Final Project.ipynb"
    notebook = nbformat.read(path, as_version=4)
    shell = InteractiveShell.instance()
    count = 0
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        count += 1
        print(f"Executing code cell {count} (notebook cell {index + 1})", flush=True)
        with capture_output() as captured:
            result = shell.run_cell(cell.source, store_history=True)
        result.raise_error()
        outputs = []
        for name in ("stdout", "stderr"):
            value = getattr(captured, name)
            if value:
                outputs.append(nbformat.v4.new_output("stream", name=name, text=value))
        for item in captured.outputs:
            outputs.append(nbformat.v4.new_output("display_data", data=item.data, metadata=item.metadata))
        cell.outputs = outputs
        cell.execution_count = count
    notebook.metadata["execution"] = {"method": "in-process IPython; fresh script process",
        "executed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "code_cells_executed": count}
    nbformat.validate(notebook)
    temporary = path.with_suffix(".ipynb.part")
    nbformat.write(notebook, temporary)
    temporary.replace(path)
    print(f"Saved {count} executed code cells: {path.name}")


if __name__ == "__main__":
    main()
