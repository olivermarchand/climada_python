"""
define save functionalities
"""

import os
import pickle
import logging

from climada.util.constants import SAVE_DIR

LOGGER = logging.getLogger(__name__)

def save(out_file_name, var):
    """Save variable with provided file name in SAVE_DIR directory
            
    Parameters
    ----------
        out_file_name (str): file name (relative to SAVE_DIR)
        var (object): variable to save in pickle format
    
    """
    try:
        with open(SAVE_DIR + out_file_name, 'wb') as file:
            pickle.dump(var, file)
    except FileNotFoundError:
        LOGGER.error('Folder not found: %s', \
                os.path.dirname(os.path.abspath(SAVE_DIR + out_file_name)))
        raise