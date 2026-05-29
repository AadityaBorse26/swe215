from setuptools import setup, find_packages

setup(
    name="pytest-valcov",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "pytest11": [
            "value_coverage = pytest_valcov.plugin",
        ],
    },
    install_requires=[
        "pytest>=6.0.0",
    ],
)
