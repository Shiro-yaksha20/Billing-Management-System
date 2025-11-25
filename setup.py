from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

import re

with open("app/__init__.py", "r") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setup(
    name="salon-billing-system",
    version=version,
    description="A desktop billing system for salons.",
    author="Jules",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "gui_scripts": [
            "salon-billing-system = main:main",
        ],
    },
)
