import logging
import os
import subprocess
import zipfile
from pathlib import Path

logger = logging.getLogger("osparc-python-main")

ENVIRONS = ['INPUT_FOLDER', 'OUTPUT_FOLDER', 'LOG_FOLDER']
input_dir, output_dir, log_dir = [ Path(os.environ.get(v, None)) for v in ENVIRONS ]


def run_cmd(cmd: str):
    subprocess.run(
        cmd.split(),
        shell=True, check=True,
        cwd=input_dir
    )
    # TODO: deal with stdout, log? and error??


def unzip_inputs():
    for filepath in list(input_dir.rglob("*.zip")):
        if zipfile.is_zipfile(filepath):
            logger.info("Unziping %s ...", filepath)
            with zipfile.ZipFile(filepath) as zf:
                zf.extractall(filepath.parent)

def ensure_main_entrypoint():
    code_files = input_dir.rglob("*.py")

    if not code_files:
        raise ValueError("No python code found")

    if len(code_files) > 1:
        code_files = list(input_dir.rglob("main.py"))
        if not code_files:
            raise ValueError("No entrypoint found (e.g. main.py)")
        if len(code_files)>1:
            raise ValueError(f"Many entrypoints found: {code_files}")

    main_py = code_files[0]
    return main_py

def ensure_requirements():
    requirements = list( input_dir.rglob("requirements.txt") )
    if len(requirements)>1:
        raise ValueError(f"Many requirements found: {requirements}")

    elif not requirements:
        # deduce requirements using pipreqs
        logger.info("Not found. Recreating requirements ...")
        requirements = input_dir / "requirements.txt"
        run_cmd(f"pipreqs --savepath={requirements} --force {input_dir}")

        # TODO log subprocess.run

    else:
        requirements = requirements[0]
    return requirements


def main():
    unzip_inputs()

    logger.info("Searching main entrypoint ...")
    main_py = ensure_main_entrypoint()
    logger.info("Found %s as main entrypoint", main_py)

    logger.info("Searching requirements ...")
    requirements = ensure_requirements()

    # TODO: take snapshot
    logger.info("Creating virtual environment ...")
    run_cmd("python3 -m venv --system-site-packages --symlinks --upgrade .venv")
    run_cmd(".venv/bin/pip install -U pip wheel setuptools")
    run_cmd(f".venv/bin/pip install -r {requirements}")

    # TODO: take snapshot
    logger.info("Executing code ...")
    run_cmd(f"venv/bin/python3 {main_py}")

    logger.info("DONE")


if __name__ == "__main__":
    main()