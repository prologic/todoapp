#!/usr/bin/env python

from setuptools import setup


def parse_requirements(filename):
    with open(filename, "r") as f:
        for line in f:
            if line and line[:2] not in ("#", "-e"):
                yield line.strip()


setup(
    name="todoapp",
    version="dev",
    scripts=(
        "todoapp",
    ),
    install_requires=list(parse_requirements("requirements.txt")),
)
