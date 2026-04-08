from setuptools import find_packages, setup

setup(
    name="abc-scanner",
    version="0.1.0",
    description="Nástroje pro skeny časopisu ABC",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "pymupdf>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "abc-scanner=abc_scanner.cli:main",
        ],
    },
)
