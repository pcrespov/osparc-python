import json
import os
import sys
import zipfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

current_dir = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent

validation_dir = (current_dir / "..").resolve() / "validation"
input_dir = validation_dir / "input"
sample_dir = validation_dir / "sample"


def as_code():
    code_file = validation_dir / "sample" / "main.py"

    with open("input.json", "wt") as fh:
        json.dump({
            'code': code_file.read_text(),
            'input_data': code_file.name
        }, fh, indent=2)


def zipdir(dirpath: Path, ziph: zipfile.ZipFile):
    """ Zips directory and archives files relative to dirpath
    """
    for root, dirs, files in os.walk(dirpath):
        for filename in files:
            filepath = os.path.join(root, filename)
            ziph.write(filepath, arcname=os.path.relpath(filepath, dirpath))
        dirs[:] = [name for name in dirs if not name.startswith(".")]


def main():
    target =  input_dir/"sample.zip"
    log.info("Zipping %s", target)

    with zipfile.ZipFile(str(target), "w", zipfile.ZIP_DEFLATED) as zh:
        zipdir(sample_dir, zh)


if __name__ == "__main__":
    main()