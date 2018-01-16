"""
Functionalities to handle HDF5 files. Used for MATLAB files as well.
"""

from scipy import sparse
import numpy as np
import h5py

def read(file_name, with_refs=False):
    """Load a hdf5 data structure from a file.

        Parameters
        ----------
            file_name: file to load
            with_refs: enable loading of the references. Default is unset,
                since it increments the execution time considerably.

        Returns
        -------
            contents: dictionary structure containing all the variables.

        Examples
        --------
            >>> contents = read("/pathto/dummy.mat")
            Contents contains the Matlab data in a dictionary.
            >>> contents = read("/pathto/dummy.mat", True)
            Contents contains the Matlab data and its reference in a
            dictionary.

        Raises
        ------
            Exception while reading
        """
    def get_group(group):
        '''Recursive function to get variables from a group.'''
        contents = {}
        for name, obj in list(group.items()):
            if isinstance(obj, h5py.Dataset):
                contents[name] = np.array(obj)
            elif isinstance(obj, h5py.Group):
                # it is a group, so call self recursively
                if with_refs or name != "#refs#":
                    contents[name] = get_group(obj)
            # other objects such as links are ignored
        return contents

    try:
        file = h5py.File(file_name, 'r')
        contents = get_group(file)
        file.close()
        return contents
    except Exception:
        print('Error reading ' + file_name)
        raise

def get_string(array):
    """Form string from input array of unisgned integers.

        Parameters
        ----------
            array: array of integers

        Returns
        -------
            string
    """
    return u''.join(chr(c) for c in array)

def get_string_from_ref(file_name, var):
    """Form string from a reference HDF5 variable of the given file.

        Parameters
        ----------
            file_name: matlab file name
            var: HDF5 reference variable

        Returns
        -------
            string
    """
    file = h5py.File(file_name, 'r')
    obj = file[var]
    return get_string(obj)

def get_sparse_mat(mat_dict, shape):
    """Form sparse matrix from input hdf5 sparse matrix data type.

        Parameters
        ----------
            mat_dict: dictionary containing the sparse matrix information.
            shape: tuple describing output matrix shape.

        Returns
        -------
            sparse csc matrix
    """
    # Check if input has all the necessary data of a sparse matrix
    if ('data' not in mat_dict) or ('ir' not in mat_dict) or \
    ('jc' not in mat_dict):
        raise ValueError('Input data is not a sparse matrix.')

    return sparse.csc_matrix((mat_dict['data'], mat_dict['ir'], \
                              mat_dict['jc']), shape)