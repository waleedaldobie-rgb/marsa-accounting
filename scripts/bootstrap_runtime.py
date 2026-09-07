"""One-command local bootstrap for the real Django/PostgreSQL environment.

Run this only after installing requirements and starting PostgreSQL:
    python scripts/bootstrap_runtime.py
"""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

def run(*args):
    print("$", " ".join(args))
    subprocess.run([sys.executable, *args], check=True)

run("manage.py", "check")
run("manage.py", "makemigrations")
run("manage.py", "migrate")
run("manage.py", "test")
