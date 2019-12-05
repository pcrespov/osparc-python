import json
import os
from pathlib import Path

import yaml

indir = Path(os.environ['INPUT_FOLDER']).resolve()
outdir = Path(os.environ['OUTPUT_FOLDER']).resolve()

with open(outdir / 'output_data.yml', 'wt') as fh:
    data = json.loads((indir / "input.json").read_text())
    yaml.safe_dump(data, fh)
