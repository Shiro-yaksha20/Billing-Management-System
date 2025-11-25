from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="salon-billing-system",
    version="1.0.0",
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
