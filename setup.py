"""A setuptools based setup module.
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
import os

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the data recursively from the data folder
def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            if filename != '.DS_Store':
                paths.append(os.path.join('..', path, filename))
    return paths

extra_files = package_files(here + '/data/')
# Add configuration files
extra_files.append(here + '/climada/conf/defaults.conf')

setup(
    name='climada',

    version='1.4.0',

    description='CLIMADA in Python',

    long_description=long_description,

    url='https://github.com/davidnbresch/climada_python',

    author='ETH',

    license='GNU General Public License',

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Topic :: Climate Adaptation',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='climate adaptation',

    packages=find_packages(where='.'),

    install_requires=[
        'bottleneck>=1.3.2',
        'cfgrib>=0.9.7.7',
        'cython>=0.28.2',
        'dask>=2.25.0',
        'fsspec>=0.3.3',  # Needed for dask dataframes
        'fiona>=1.8.13.post1',
        'gdal==3.0.4',
        'geopandas>=0.5.0',
        'rtree==0.8.3',  # Optional geopandas dependency
        'h5py>=2.10.0,<3.*',
        'haversine>=2.3.0',
        'nbconvert>=5.6.1',
        'nbformat>=4.4',
        'netcdf4>=1.5.4',
        'numba>=0.51.2',
        'numpy>=1.18.1',
        'matplotlib>=3.1.2',
        # Pandas can be a bit of a problem:
        #'pandas==1.0.5',
        #'pandas-datareader==0.8.1',
        'pandas>=0.23.4',
        'pandas_datareader>=0.7.0',
        'pillow>=7.0.0',
        'pint>=0.15',
        'pyproj>=2.6.0',
        'tables>=3.6.1',
        'rasterio>=1.1.5',
        'scikit-learn>=0.23.2',
        'statsmodels>=0.11.1',
        'tabulate>=0.8.7',
        'tqdm>=4.48.2',
        'xarray==0.13.0',
        'xlrd>=1.1.0',
        'xlsxwriter>=1.1.7',
        'contextily>=1.0.0',
        'iso3166>=1.0.1',
        'overpy>=0.4',
        'pathos>=0.2.6',
        'pybufrkit>=0.2.17',
        'xmlrunner>=1.7.7',
    ],

    package_data={'': extra_files},

    include_package_data=True
)
