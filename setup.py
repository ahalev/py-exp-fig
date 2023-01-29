from pathlib import Path
from setuptools import setup, find_packages

DESCRIPTION = 'A yaml-based configuration for reproducible python experiments.'
VERSION = '0.1'
MAINTAINER = "Avishai Halev"
MAINTAINER_EMAIL = "avishaihalev@gmail.com"
LICENSE = "MIT License"
PROJECT_URLS = {}

setup(
    name="expfig",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.6",
    version=VERSION,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    project_urls=PROJECT_URLS,
    description=DESCRIPTION,
    license=LICENSE,
    long_description=(Path(__file__).parent / "README.md").read_text(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "pandas",
        "pyyaml"
    ],
)
