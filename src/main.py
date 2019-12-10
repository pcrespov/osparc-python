import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("osparc-python-main")


ENVIRONS = ['INPUT_FOLDER', 'OUTPUT_FOLDER', 'LOG_FOLDER']
input_dir, output_dir, log_dir = [ Path(os.environ.get(v, None)) for v in ENVIRONS ]



def copy(src, dest):
    try:
        src, dest = str(src), str(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns('*.zip', '__pycache__', '.*'))
    except OSError as err:
        # If the error was caused because the source wasn't a directory
        if err.errno == shutil.errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            logger.error('Directory not copied. Error: %s', err)

def clean_dir(dirpath: Path):
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))



def run_cmd(cmd: str):
    subprocess.run(
        cmd.split(),
        shell=False, check=True,
        cwd=input_dir
    )
    # TODO: deal with stdout, log? and error??


def unzip_dir(parent: Path):
    for filepath in list(parent.rglob("*.zip")):
        if zipfile.is_zipfile(filepath):
            with zipfile.ZipFile(filepath) as zf:
                zf.extractall(filepath.parent)


def zipdir(dirpath: Path, ziph: zipfile.ZipFile):
    """ Zips directory and archives files relative to dirpath
    """
    for root, dirs, files in os.walk(dirpath):
        for filename in files:
            filepath = os.path.join(root, filename)
            ziph.write(filepath, arcname=os.path.relpath(filepath, dirpath))
        dirs[:] = [name for name in dirs if not name.startswith(".")]


def ensure_main_entrypoint():
    code_files = list(input_dir.rglob("*.py"))

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



def setup():
    logger.info("Cleaning output ...")
    clean_dir(output_dir)

    logger.info("Processing input ...")
    unzip_dir(input_dir)

    #logger.info("Copying input to output ...")
    #copy(input_dir, output_dir)

    logger.info("Searching main entrypoint ...")
    main_py = ensure_main_entrypoint()
    logger.info("Found %s as main entrypoint", main_py)

    logger.info("Searching requirements ...")
    requirements = ensure_requirements()

    logger.info("Preparing launch script ...")
    venv_dir = Path("~.venv").expanduser()
    with open("main.sh", 'wt') as fh:
        print('echo "Creating virtual environment ..."', file=fh)
        print(f"python3 -m venv --system-site-packages --symlinks --upgrade {venv_dir}", file=fh)
        print(f"{venv_dir}/bin/pip install -U pip wheel setuptools", file=fh)
        print(f"{venv_dir}/bin/pip install -r {requirements}", file=fh)
        print(f'echo "Executing code {main_py.name}..."', file=fh)
        print(f"{venv_dir}/bin/python3 {main_py}", file=fh)
        print('echo "DONE ..."', file=fh)

    # # TODO: take snapshot
    # logger.info("Creating virtual environment ...")
    # run_cmd("python3 -m venv --system-site-packages --symlinks --upgrade .venv")
    # run_cmd(".venv/bin/pip install -U pip wheel setuptools")
    # run_cmd(f".venv/bin/pip install -r {requirements}")

    # # TODO: take snapshot
    # logger.info("Executing code ...")
    # run_cmd(f".venv/bin/python3 {main_py}")


def teardown():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(f"{tmpdir}/output.zip")
        with zipfile.ZipFile(str(target), "w", zipfile.ZIP_DEFLATED) as zh:
            zipdir(output_dir, zh)

        clean_dir(output_dir)
        copy(target, output_dir)


if __name__ == "__main__":
    action = 'setup' if len(sys.argv)==1 else sys.argv[1]
    try:
        if action == 'setup':
            setup()
        else:
            teardown()
    except Exception as err: # pylint: disable=broad-except
        logger.error("%s . Stopping %s", err, action)
