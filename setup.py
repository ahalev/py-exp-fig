from pathlib import Path
from setuptools import setup, find_packages

DESCRIPTION = 'A yaml-based configuration for reproducible python experiments.'
VERSION = '1.0.2'
MAINTAINER = 'Avishai Halev'
MAINTAINER_EMAIL = 'avishaihalev@gmail.com'
LICENSE = 'MIT License'
PROJECT_URLS = {
    'Source Code': f'https://github.com/ahalev/experiment-config/tree/v{VERSION}'
}

EXTRAS = {
    'dev': ['numpy', 'pytest'],
    'pandas': ['pandas'],
}

EXTRAS['all'] = sum(EXTRAS.values(), [])


setup(
    name='experiment-config',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    python_requires='>=3.6',
    version=VERSION,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    project_urls=PROJECT_URLS,
    description=DESCRIPTION,
    license=LICENSE,
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    install_requires=[
        'pyyaml'
    ],
    extras_require=EXTRAS

)
