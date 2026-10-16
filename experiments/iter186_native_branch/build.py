"""Build only the small adapter against an explicitly installed OMPL prefix."""

import argparse
from pathlib import Path
import subprocess

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--prefix", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    prefix = a.prefix.resolve()
    subprocess.run(
        [
            "clang++",
            "-std=c++17",
            "-O2",
            "-shared",
            "-fPIC",
            "-MMD",
            "-MF",
            str(a.output.resolve()) + ".d",
            str(Path(__file__).with_name("bridge.cpp")),
            "-I",
            str(prefix / "include/ompl-2.0"),
            "-I",
            str(prefix / "include/eigen3"),
            "-I",
            str(prefix / "include"),
            "-L",
            str(prefix / "lib"),
            "-lompl",
            "-Wl,-rpath," + str(prefix / "lib"),
            "-o",
            str(a.output.resolve()),
        ],
        check=True,
    )
