from setuptools import setup, find_packages

setup(
    name='json2json',
    version='0.1.0',
    author='rdgoite',
    author_email='rodrey@ebi.ac.uk',
    description='A tool for converting JSON documents to another JSON document format.',
    url='https://github.com/ebi-ait/ingest-archiver/tree/master/conversion',
    packages=find_packages(include=('conversion',)),
    python_requires='>=3.6'
)