import argparse
import contextlib
import difflib
import os
import random
import tempfile
import string
import subprocess
import sys


def silent_check_call(*call_args):
    with open(os.devnull, "w") as devnull:
        subprocess.check_call(*call_args,
                              stdout=devnull, stderr=subprocess.STDOUT)


def open_stdin():
    return [line.strip() for line in sys.stdin]


def open_requirements_filepath(filepath):
    if filepath == "-":
        return open_stdin()
    with open(filepath) as f:
        return [line.strip() for line in f]


def random_venv_name(num_chars=10):
    return "".join(
        random.choice(string.ascii_letters) for _ in range(num_chars))


@contextlib.contextmanager
def mkvirtualenv():
    venv_name = random_venv_name()
    venv_path = os.path.join(tempfile.gettempdir(), venv_name)
    silent_check_call(["virtualenv", venv_path])
    yield venv_path
    silent_check_call(["rm", "-rf", venv_path])


def hydrated_requirements(requirements):
    with mkvirtualenv() as venv_path:
        pip_path = "{}/bin/pip".format(venv_path)
        silent_check_call([pip_path, "install"] + requirements)
        freeze_output = subprocess.check_output([pip_path, "freeze"])
        return sorted(freeze_output.split("\n"))


def main():
    parser = argparse.ArgumentParser(
        description="Compare two different requirements.txt files.")
    parser.add_argument(
        "left", type=str,
        help="path to requirements file, can be '-' for stdin.")
    parser.add_argument(
        "right", type=str,
        help="path to requirements file, can be '-' for stdin.")

    args = parser.parse_args()

    hydrated_left = hydrated_requirements(
        open_requirements_filepath(args.left))
    hydrated_right = hydrated_requirements(
        open_requirements_filepath(args.right))

    # needs this because apparently difflib needs to look for the \n delimiter
    left_for_difflib = [x + "\n" for x in hydrated_left]
    right_for_difflib = [x + "\n" for x in hydrated_right]

    diff_lines = difflib.unified_diff(
        left_for_difflib, right_for_difflib,
        args.left, args.right
    )
    sys.stdout.writelines(diff_lines)


if __name__ == "__main__":
    main()
