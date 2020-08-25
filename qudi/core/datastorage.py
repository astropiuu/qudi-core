# -*- coding: utf-8 -*-

"""
This file contains data storage utilities for Qudi.

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import os
import re
import copy
import numpy as np
import matplotlib.pyplot as plt
from abc import ABCMeta, abstractmethod
from enum import Enum
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
from qudi.core.util.paths import get_userdata_dir
from qudi.core.application import Qudi


def get_default_data_dir(create_missing=False):
    """ Returns the qudi default data root directory. Will first try to interface with the running
    qudi instance and extract the desired root directory from the loaded config. If this fails, fall
    back to the default qudi userdata directory (usually user home dir).

    @property:
    """
    qudi = Qudi.instance()
    if qudi is None:
        path = os.path.join(get_userdata_dir(create_missing=create_missing), 'Data')
    else:
        path = qudi.configuration.default_data_dir
        if path is None:
            path = os.path.join(get_userdata_dir(create_missing=create_missing), 'Data')
    if create_missing and not os.path.exists(path):
        os.makedirs(path)
    return path


def get_daily_data_directory(root=None, timestamp=None, create_missing=True):
    """ Returns a path to a directory for storing data from today.

    The directory structure will have the form: <root>/<YYYY>/<MM>/<YYYYMMDD>/

    If not root directory is given, this method will first try to interface with a running qudi
    instance and extract the desired root directory from the loaded config. If this fails, it will
    fall back to the default qudi userdata directory (usually user home dir).

    @param str root: optional, explicit root path for daily directory structure
    @param datetime.datetime timestamp: optional, Timestamp for which to create daily directory
    @param bool create_missing: optional, indicate if a directory should be created (True) or not
                                (False)
    """
    # Determine root directory
    if root is None:
        root = get_default_data_dir(create_missing=create_missing)

    # Create timestamp if omitted
    if not isinstance(timestamp, datetime):
        timestamp = datetime.now()

    # Determine daily directory path
    leaf_dir = '{0:d}{1:d}{2:d}'.format(timestamp.year, timestamp.month, timestamp.day)
    daily_dir = os.path.join(root, str(timestamp.year), str(timestamp.month), leaf_dir)

    # Create directory if necessary
    if not os.path.exists(daily_dir):
        if create_missing:
            os.makedirs(daily_dir, exist_ok=True)
        else:
            raise NotADirectoryError('Daily directory not found.')
    return daily_dir


class ImageFormat(Enum):
    """ Image format to use for saving data thumbnails.
    """
    PNG = '.png'
    PDF = '.pdf'


class DataFormat(Enum):
    """ File format for saving data to disk.
    """
    TEXT = 0
    CSV = 1
    NPY = 2
    XML = 3
    HDF5 = 4


class DataStorageBase(metaclass=ABCMeta):
    """ Base helper class to store (measurement)data on disk. Creates daily directory structure to
    store data in by default.
    """
    __global_parameters = dict()

    def __init__(self, *, root_dir=None, sub_directory=None, file_extension='.dat',
                 use_daily_dir=True, include_global_parameters=True, image_format=ImageFormat.PNG):
        """
        @param str root_dir: optional, root-directory path for daily directory tree
        @param str sub_directory: optional, sub-directory name to use within daily data directory
        @param str file_extension: optional, the file extension to be used for the data file
        @param bool use_daily_dir: optional, flag indicating daily sub-directory usage
        @param bool include_global_parameters: optional, flag indicating saving of global parameters
        @param ImageFormat image_format: optional, image file format Enum
        """
        if root_dir is None:
            self.root_dir = get_default_data_dir(create_missing=False)
        else:
            self.root_dir = root_dir

        if isinstance(file_extension, str):
            if file_extension:
                self.file_extension = '.' * (not file_extension.startswith('.')) + file_extension
        else:
            self.file_extension = None

        if not isinstance(image_format, ImageFormat):
            raise TypeError('image_format must be ImageFormat Enum')

        self.sub_directory = sub_directory
        self.image_format = image_format
        self.use_daily_dir = bool(use_daily_dir)
        self.include_global_parameters = bool(include_global_parameters)
        return

    def get_data_directory(self, timestamp=None, create_missing=True):
        """ Create and return directory path to save data in.

        @param datetime.datetime timestamp: optional, Timestamp for which to create daily directory
        @param bool create_missing: optional, indicate if a directory should be created (True) or
                                    not (False)
        """
        if self.use_daily_dir:
            daily = get_daily_data_directory(root=self.root_dir,
                                             timestamp=timestamp,
                                             create_missing=create_missing)
            path = daily if self.sub_directory is None else os.path.join(daily, self.sub_directory)
        else:
            path = os.path.join(self.root_dir, self.sub_directory)
        if create_missing:
            os.makedirs(path, exist_ok=True)
        return path

    def create_file_path(self, timestamp=None, filename=None, nametag=None):
        """
        """
        if filename is None:
            if timestamp is None:
                timestamp = datetime.now()
            if nametag is None:
                filename = timestamp.strftime('%Y%m%d-%H%M-%S')
            else:
                filename = '{0}_{1}'.format(timestamp.strftime('%Y%m%d-%H%M-%S'), nametag)
        if self.file_extension is not None and not filename.endswith(self.file_extension):
            filename += self.file_extension
        return os.path.join(self.get_data_directory(timestamp=timestamp, create_missing=True),
                            filename)

    def save_thumbnail(self, mpl_figure, timestamp=None, filename=None, nametag=None):
        # Create file path
        file_path = self.create_file_path(timestamp=timestamp,
                                          filename=filename,
                                          nametag=nametag,
                                          file_extension=self.image_format.value())

        if self.image_format is ImageFormat.PDF:
            # Create the PdfPages object to which we will save the pages:
            with PdfPages(file_path) as pdf:
                pdf.savefig(mpl_figure, bbox_inches='tight', pad_inches=0.05)
        elif self.image_format is ImageFormat.PNG:
            # save the image as PNG
            mpl_figure.savefig(file_path, bbox_inches='tight', pad_inches=0.05)
        else:
            raise Exception('Unknown image format selected: "{0}"'.format(self.image_format))

        # close matplotlib figure and return
        plt.close(mpl_figure)
        return file_path

    @abstractmethod
    def save_data(self, *args, **kwargs):
        pass

    @abstractmethod
    def load_data(self, *args, **kwargs):
        """
        @return np.ndarray, dict, tuple: Data as numpy array, extracted parameters, column headers
        """
        pass
        # FIXME: This is not in a satisfying condition yet. Please improve, test and remove error.
        # raise Exception('Loading data is not fully implemented, yet.')
        # parameters = dict()
        # column_header = ''
        # if self.data_format in (DataFormat.TEXT, DataFormat.CSV):
        #     index = 0
        #     in_params = False
        #     in_data = False
        #     with open(file_path, 'r', newline='') as file:
        #         for line in file:
        #             if not line.startswith(self.comments):
        #                 file.seek(index)
        #                 break
        #             if line.endswith('Parameters:\n'):
        #                 in_params = True
        #             elif line.endswith('Data:\n'):
        #                 in_data = True
        #             if in_data and not line[len(self.comments):].startswith('====='):
        #                 column_header += line[len(self.comments):]
        #             elif in_params and ': ' in line:
        #                 clean_param = line[len(self.comments):].strip()
        #                 name, value_str = clean_param.rsplit(': ', 1)
        #                 if self.__int_regex.match(value_str):
        #                     parameters[name] = int(value_str)
        #                 elif self.__float_regex.match(value_str):
        #                     parameters[name] = float(value_str)
        #                 else:
        #                     parameters[name] = str(value_str)
        #         reader = csv.reader(file, delimiter=self.delimiter)
        #         data_array = np.asarray([data for data in reader])
        #         if data_array.ndim > 1:
        #             if data_array.shape[1] == 1:
        #                 data_array = data_array[:, 0]
        #                 headers = (column_header.strip(),) if column_header else tuple()
        #             else:
        #                 headers = tuple(
        #                     it.strip() for it in column_header.split(self.delimiter) if it.strip())
        #                 if len(headers) != data_array.shape[1]:
        #                     headers = (column_header.strip(),) if column_header else tuple()
        # return data_array, parameters, headers

    @classmethod
    def get_global_parameters(cls):
        """ Return a copy of the global parameters dict.
        """
        return cls._global_parameters.copy()

    @classmethod
    def set_global_parameter(cls, name, value, overwrite=False):
        """ Set a single global parameter to save in all data file headers during this qudi session.
        """
        if not isinstance(name, str):
            raise TypeError('global parameter name must be str type.')
        if not overwrite and name in cls.__global_parameters:
            raise KeyError('global parameter "{0}" already set while overwrite flag is False.'
                           ''.format(name))
        cls.__global_parameters[name] = copy.deepcopy(value)
        return

    @classmethod
    def set_global_parameters(cls, params, overwrite=False):
        """ Set multiple global parameters to save in all data file headers during this qudi
        session.
        """
        if any(not isinstance(name, str) for name in params):
            raise TypeError('global parameter name must be str type.')
        if not overwrite and any(name in cls.__global_parameters for name in params):
            raise KeyError('global parameter already set while overwrite flag is False.')
        for name, value in params.items():
            cls.__global_parameters[name] = copy.deepcopy(value)
        return

    @classmethod
    def remove_global_parameter(cls, name):
        """ Remove a global parameter. Does not raise an error.
        """
        cls.__global_parameters.pop(name, None)
        return


class TextDataStorage(DataStorageBase):
    """ Helper class to store (measurement)data on disk in a daily directory as text file.
    Data will always be saved in a tabular format with column headers. Single/Multiple rows are
    appendable.
    """

    # Regular expressions to automatically determine number format
    # __int_regex = re.compile(r'\A[+-]?\d+\Z')
    # __float_regex = re.compile(r'\A[+-]?\d+.\d+([eE][+-]?\d+)?\Z')

    def __init__(self, *, column_headers=None, number_format='%.18e', comments='# ', delimiter='\t',
                 **kwargs):
        """
        @param tuple|str column_headers: optional, iterable of strings containing column headers.
                                         If a single string is given, write it to file header
                                         without formatting.
        @param str|tuple number_format: optional, number format specifier (mini-language) for text
                                        files. Can be iterable of format specifiers for each column.
        @param str comments: optional, string to put at the beginning of comment and header lines
        @param str delimiter: optional, column delimiter used in text files
        @param kwargs: optional, for additional keyword arguments see DataStorageBase.__init__
        """
        super().__init__(**kwargs)

        if isinstance(column_headers, str):
            self.column_headers = column_headers
        elif any(not isinstance(header, str) for header in column_headers):
            raise TypeError('Data column headers must be str type.')
        else:
            self.column_headers = tuple(column_headers)

        if not delimiter or not isinstance(delimiter, str):
            raise ValueError('Parameter "delimiter" must be non-empty string.')

        self.number_format = number_format
        self.comments = comments if isinstance(comments, str) else None
        self.delimiter = delimiter
        self._current_data_file = None

    def create_header(self, parameters, timestamp, include_column_headers=True):
        """
        """
        # Gather all parameters (both global and provided) into a single dict if needed
        if self.include_global_parameters:
            all_parameters = self.__global_parameters.copy()
            all_parameters.update(parameters)
        else:
            all_parameters = parameters.copy()

        header_lines = list()
        header_lines.append('Saved Data on {0}'.format(timestamp.strftime('%d.%m.%Y at %Hh%Mm%Ss')))
        header_lines.append('')
        if all_parameters:
            header_lines.append('Parameters:')
            header_lines.append('===========')
            for param, value in all_parameters.items():
                if isinstance(value, (float, np.floating)):
                    header_lines.append('{0}: {1:.18e}'.format(param, value))
                elif isinstance(value, (int, np.integer)):
                    header_lines.append('{0}: {1:d}'.format(param, value))
                else:
                    header_lines.append('{0}: {1}'.format(param, value))
            header_lines.append('')
        header_lines.append('Data:')
        header_lines.append('=====')
        if self.column_headers is not None and include_column_headers:
            if isinstance(self.column_headers, str):
                header_lines.append(self.column_headers)
            else:
                header_lines.append(self.delimiter.join(self.column_headers))
        header_lines.append('')

        line_sep = '\n{0}'.format('' if self.comments is None else self.comments)
        return line_sep.join(header_lines)

    def new_data_file(self, *, parameters=None, filename=None, nametag=None, timestamp=None):
        # Create timestamp if missing
        if timestamp is None:
            timestamp = datetime.now()
        # Determine full file path and create containing directories if needed
        file_path = self.create_file_path(timestamp=timestamp, filename=filename, nametag=nametag)
        # Create header
        header = self.create_header(parameters=parameters, timestamp=timestamp)
        with open(file_path, 'w') as file:
            file.write(header)
        self._current_data_file = file_path
        return file_path, timestamp

    def append_data_file(self, data, file_path=None):
        """
        """
        if file_path is None:
            file_path = self._current_data_file

        if file_path is None or not os.path.isfile(file_path):
            raise FileNotFoundError('No file created for writing data. Call "new_data_file" before '
                                    'trying to append.')
        # Append data to file
        with open(file_path, 'a') as file:
            # Write numpy data array
            if data.ndim == 1:
                np.savetxt(file,
                           np.expand_dims(data, axis=0),
                           delimiter=self.delimiter,
                           fmt=self.number_format)
            else:
                np.savetxt(file, data, delimiter=self.delimiter, fmt=self.number_format)
        return (1, data.shape[0]) if data.ndim == 1 else data.shape

    def save_data(self, data, *, parameters=None, filename=None, nametag=None, timestamp=None):
        """
        """
        # Create new data file (overwrite old one if it exists)
        file_path, timestamp = self.new_data_file(parameters=parameters,
                                                  filename=filename,
                                                  nametag=nametag,
                                                  timestamp=timestamp)
        # Append data to file
        rows, columns = self.append_data_file(data)
        return file_path, timestamp, (rows, columns)

    def load_data(self, file_path):
        pass


class CsvDataStorage(TextDataStorage):
    """ Helper class to store (measurement)data on disk as CSV file.
    This is a specialized sub-class of TextDataStorage that uses commas as delimiter and includes
    column headers uncommented in the first row of data. This is the standard for importing a table
    into e.g. MS Excel.
    """
    def __init__(self, **kwargs):
        """
        @param tuple|str column_headers: optional, iterable of strings containing column headers.
                                         If a single string is given, write it to file header
                                         without formatting.
        @param str|tuple number_format: optional, number format specifier (mini-language) for text
                                        files. Can be iterable of format specifiers for each column.
        @param str comments: optional, string to put at the beginning of comment and header lines
        @param str delimiter: optional, column delimiter used in text files
        @param kwargs: optional, for additional keyword arguments see DataStorageBase.__init__
        """
        kwargs['delimiter'] = ','
        super().__init__(**kwargs)

    def create_header(self, parameters, timestamp):
        """
        """
        if isinstance(self.column_headers, str):
            header = super().create_header(parameters, timestamp, True)
        else:
            header = super().create_header(parameters, timestamp, False)
            if self.column_headers is not None:
                header += ','.join(self.column_headers) + '\n'
        return header

    def load_data(self, file_path):
        pass


class NumpyDataStorage(DataStorageBase):
    """ Helper class to store (measurement)data on disk as binary .npy file.
    """
    def __init__(self, **kwargs):
        kwargs['file_extension'] = '.npy'
        kwargs['comments'] = None
        super().__init__(**kwargs)

    def save_data(self, data, *, parameters=None, filename=None, nametag=None, timestamp=None):
        """
        """
        # Create new data file (overwrite old one if it exists)
        file_path, timestamp = self.new_data_file(parameters=parameters,
                                                  filename=filename,
                                                  nametag=nametag,
                                                  timestamp=timestamp)
        # Append data to file
        rows, columns = self.append_data_file(data)
        return file_path, timestamp, (rows, columns)

    def create_header(self, parameters, timestamp, data_filename, include_column_headers=True):
        """
        """
        # Gather all parameters (both global and provided) into a single dict if needed
        if self.include_global_parameters:
            all_parameters = self.__global_parameters.copy()
            all_parameters.update(parameters)
        else:
            all_parameters = parameters.copy()

        header_lines = list()
        header_lines.append(
            'Saved Data on {0} into {1}'.format(timestamp.strftime('%d.%m.%Y at %Hh%Mm%Ss'),
                                                data_filename
                                                )
        )
        header_lines.append('')
        if all_parameters:
            header_lines.append('Parameters:')
            header_lines.append('===========')
            for param, value in all_parameters.items():
                if isinstance(value, (float, np.floating)):
                    header_lines.append('{0}: {1:.18e}'.format(param, value))
                elif isinstance(value, (int, np.integer)):
                    header_lines.append('{0}: {1:d}'.format(param, value))
                else:
                    header_lines.append('{0}: {1}'.format(param, value))
        if self.column_headers is not None and include_column_headers:
            header_lines.append('')
            header_lines.append('Column headers:')
            header_lines.append('=====')
            if isinstance(self.column_headers, str):
                header_lines.append(self.column_headers)
            else:
                header_lines.append(self.delimiter.join(self.column_headers))
        header_lines.append('')

        line_sep = '\n{0}'.format('' if self.comments is None else self.comments)
        return line_sep.join(header_lines)

    def save_data(self, data, *, parameters=None, filename=None, nametag=None, timestamp=None):
        """
        """
        # Create timestamp if missing
        if timestamp is None:
            timestamp = datetime.now()

        # Determine full file path and create containing directories if needed
        file_path = self.create_file_path(timestamp=timestamp, filename=filename, nametag=nametag)
        # Write out data file
        with open(file_path, 'wb') as file:
            # Write numpy data array in binary format
            np.save(file, data, allow_pickle=False, fix_imports=False)

        # Create header to save in a separate text file
        param_file_path = file_path.rsplit('.', 1)[0] + '_parameters.txt'
        header = self.create_header(parameters=parameters,
                                    timestamp=timestamp,
                                    data_filename=os.path.split(file_path)[-1])
        with open(param_file_path, 'w') as file:
            file.write(header)
        return file_path, timestamp, data.shape

    def load_data(self, file_path):
        pass