import sys
from pathlib import Path
import json

current_dir = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent
code_file = current_dir / "sample.py"

with open("input.json", "wt") as fh:
    json.dump({
        'code': code_file.read_text(),
        'input_data': code_file.name
    }, fh, indent=2)
