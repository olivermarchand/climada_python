"""
Define DiscRates.
"""

__all__ = ['DiscRates']

import os
import concurrent.futures
import itertools
from array import array
import numpy as np

from climada.entity.disc_rates.source_excel import read as read_excel
from climada.entity.disc_rates.source_mat import read as read_mat
from climada.util.files_handler import to_str_list, get_file_names
import climada.util.checker as check
from climada.entity.tag import Tag

class DiscRates(object):
    """Contains discount rates.

    Attributes
    ----------
        tag (Taf): information about the source data
        years (np.array): years
        rates (np.array): discount rates for each year
    """

    def __init__(self, file_name='', description=''):
        """Fill values from file, if provided.

        Parameters
        ----------
            file_name (str or list(str), optional): file name(s) or folder name 
                containing the files to read
            description (str or list(str), optional): description of the data

        Raises
        ------
            ValueError

        Examples
        --------
            >>> disc_rates = DiscRates()
            >>> disc_rates.years = np.array([2000, 2001])
            >>> disc_rates.rates = np.array([0.02, 0.02])
            >>> disc_rates.check()
            Fill discount rates with values and check consistency data.
        """
        self.tag = Tag(file_name, description)
        # Following values are given for each defined year
        self.years = np.array([], np.int64)
        self.rates = np.array([], np.float64)

        # Load values from file_name if provided
        if file_name != '':
            self.load(file_name, description)

    def check(self):
        """Check instance attributes.

        Raises
        ------
            ValueError
        """
        check.size(len(self.years), self.rates, 'DiscRates.rates')

    def load(self, file_name, description=''):
        """Read and check.

        Parameters
        ----------
            file_name (str or list(str)): file name(s) or folder name 
                containing the files to read
            description (str or list(str), optional): description of the data

        Raises
        ------
            ValueError
        """
        self.read(file_name, description)
        self.check()

    def read(self, files, descriptions=''):
        """Read exposures in parallel through files.

        Parameters
        ----------
            files (str or list(str)): file name(s) or folder name 
                containing the files to read
            descriptions (str or list(str), optional): description of the data

        Raises
        ------
            ValueError
        """
        # Construct absolute path file names
        all_files = get_file_names(files)
        num_files = len(all_files)
        desc_list = to_str_list(num_files, descriptions, 'descriptions')
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for exp_part in executor.map(_wrap_read_one, \
                    itertools.repeat(DiscRates(), num_files), all_files, \
                    desc_list):
                self.append(exp_part)

    def append(self, disc_rates):
        """Append vulnerabilities of input ImpactFuncs to current ImpactFuncs.
        Overvrite vulnerability if same id.
        
        Parameters
        ----------
            impact_funcs (ImpactFuncs): ImpactFuncs instance to append

        Raises
        ------
            ValueError
        """
        self.check()
        disc_rates.check()
        if self.years.size == 0:
            self.__dict__ = disc_rates.__dict__.copy()
            return
        
        self.tag.append(disc_rates.tag)
        
        new_year = array('l')
        new_rate = array('d')
        for year, rate in zip(disc_rates.years, disc_rates.rates):
            found = np.where(year == self.years)[0]
            if found.size > 0:
                self.rates[found[0]] = rate
            else:
                new_year.append(year)
                new_rate.append(rate)
        
        self.years = np.append(self.years, new_year).astype(int)
        self.rates = np.append(self.rates, new_rate)

    def _read_one(self, file_name, description=''):
        """Read input file.

        Parameters
        ----------
            file_name (str): name of the source file
            description (str, optional): description of the source data

        Raises
        ------
            ValueError
        """
        extension = os.path.splitext(file_name)[1]
        if extension == '.mat':
            read_mat(self, file_name, description)
        elif (extension == '.xlsx') or (extension == '.xls'):
            read_excel(self, file_name, description)
        else:
            raise TypeError('Input file extension not supported: %s.' % \
                            extension)
        return self

def _wrap_read_one(disc_rates, file, description=''):
    return disc_rates._read_one(file, description)