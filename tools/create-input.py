import sys
from pathlib import Path
import json

current_dir = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent
validation_dir = (current_dir / "..").resolve()

code_file = validation_dir / "sample" / "src" / "Example_PurePython_Postpro_Osparc.py"

with open("input.json", "wt") as fh:
    json.dump({
        'code': code_file.read_text(),
        'input_data': code_file.name
    }, fh, indent=2)
