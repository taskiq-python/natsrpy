# ruff: noqa
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def main():
    subprocess.run(["maturin", "dev", "--uv"], cwd=ROOT_DIR, check=True)
    os.execvpe(
        "stubtest",
        ["--ignore-disjoint-bases", "--ignore-missing-stub", "natsrpy._natsrpy_rs"],
        env=os.environ,
    )


if __name__ == "__main__":
    main()
