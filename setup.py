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
        'bottleneck==1.3.2',
        'cartopy', # conda!
        'cloudpickle', # install_test
        'contextily==1.0rc2',
        'dask', # conda
        'descartes',
        #'earthengine_api==0.1.210', # ee, conda!
        'fiona', # conda
        'fsspec>=0.3.6', # < dask
        'gdal', # conda!
        'geopandas', # conda
        'h5py', # conda
        'haversine==2.1.1',
        'iso3166==1.0',
        'matplotlib', # conda
        'mercantile',
        'multiprocess==0.70.7',
        'nbconvert==5.5.0',
        'nbformat==4.4',
        'netCDF4', # conda!
        'numba', # conda!
        'numpy', # conda+
        'overpy==0.4',
        'pandas', # conda
        'pandas_datareader', # conda
        'pathos==0.2.3',
        'pillow==6.2.2', # PIL 7.0 has a conflict with libtiff 4.0 which is necessary for - at least - Windows
        'pint==0.9',
        'ppft==1.6.4.9',
        'pyproj', # conda
        'pyshp', # conda
        'rasterio', # conda
        'requests', # conda
        'rtree==0.8.3', # < geopandas.overlay
        'scikit-learn', # conda
        'scipy', # conda+
        'shapely', # conda
        'six==1.13.0', #
        'statsmodels==0.11.1',
        'tables', # < pandas (climada.entity.measures.test.test_base.TestApply)
        'tabulate', # conda
        'toolz', # < dask
        'tqdm', # conda
        'xarray', # conda
        'xlrd', # < pandas
        'xlsxwriter', # conda
        'xmlrunner==1.7.7', # ci tests
    ],

    package_data={'': extra_files},

    include_package_data=True
)
