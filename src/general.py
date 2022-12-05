# --------------------------------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------------------------------
import builtins as __builtin__
import glob
import importlib.util
import inspect
import logging
import os
import re
import subprocess
import sys
import types
from typing import Any, Optional, Union

import pandas as pd
import pandas.io.formats.style
from IPython.core import display as ICD
from typing_extensions import Literal

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
COLORS = {    
    'purple': '\033[95m',
    'blue': '\033[94m',
    'cyan': '\033[96m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'red': '\033[91m',

    # Style.
    'bold': '\033[1m',
    'underline': '\033[4m',
    
    # Must be at the end of print statement to revert back to normal color.
    'endc': '\033[0m'
}

# --------------------------------------------------------------------------------------------------
# Methods
# --------------------------------------------------------------------------------------------------
class GeneralUtil:

    @staticmethod
    def set_option(
        max_rows: Optional[int] = 10,
        max_cols: Optional[int] = 100,
        col_width: Optional[int] = 50
    ) -> None:
        """Wrapper function for pd.set_options.

        Parameters
        ----------
        max_rows : Optional[int], optional, default 10
        max_cols : Optional[int], optional, default 100
        col_width : Optional[int], optional, default 50
        """
        pd.set_option('display.max_rows', max_rows)
        pd.set_option('display.min_rows', max_rows)
        pd.set_option('display.max_columns', max_cols)
        pd.set_option('display.max_colwidth', col_width)

    @classmethod
    def print(
        cls,
        x: Any,
        df_max_rows: Optional[int] = 10,
        color: Optional[str] = None,
        header: Union[bool, int] = False
    ) -> None:
        """Enhanced print that can display function docstrings and dataframes.

        Parameters
        ----------
        x : Any
        df_max_rows : Optional[int], optional, default 10
            Sets how many rows to show from dataframe. After printing, reset
            display.max_rows to set_option() defaults.
        color: Optional[str], optional, default None
            Print with color. Default values in `general.COLORS`.
        header : int, default 0
            Print the input in the following format:
            # ---------------------------
            # <x>
            # ---------------------------
            Note that header and color and be simutaneously set.
        """
        if isinstance(x, (pd.DataFrame, pandas.io.formats.style.Styler)):
            cls.set_option(max_rows=df_max_rows)
            ICD.display(x)
            cls.set_option()
        elif isinstance(x, types.FunctionType):
            __builtin__.print(inspect.getsource(x))
        else:
            if header and isinstance(header, bool):
                header = len(x)
                
            if color:
                x = f"{COLORS[f'{color}']}{x}{COLORS['endc']}"
            
            if header:
                if header < 0:
                    raise ValueError('header cannot be negatve.')
                __builtin__.print('# ' + '-'*header)
                __builtin__.print(f'# {x}')
                __builtin__.print('# ' + '-'*header)
            else:
                __builtin__.print(x)

    @staticmethod
    def to_csv(
        df: pd.DataFrame,
        zipname: str,
        dirname: str,
        fname: Optional[str] = None,
        method: str = 'zip',
        compresslevel: int = 9
    ) -> None:
        """Save dataframe to csv file with compression.

        Parameters
        ----------
        df : pd.DataFrame
        zipname : str
            Name of the .zip file that the dataframe will be compressed into.
        dirname : str
            Directory of where to save the .zip.
        fname : Optional[str], optional, default None
            Name of the file within the .zip file post-extraction. Default of None will have
            the same name as the zip_name.
        method : str, optional, default 'zip'
            Type of compression.
        compresslevel : int, optional, default 9
            Degree of compression where higher number indicates higher compression.
        """
        # Process arguments.
        if dirname[-1] == '/':
            dirname = dirname[:-1]
        if re.search('\.csv', zipname):
            zipname = re.sub('\.csv', '', zipname)
        if not fname:
            fname = zipname

        compress_param = {
            'archive_name': f'{fname}.csv',
            'method': method,
            'compresslevel': compresslevel
        }
        df.to_csv(f'{dirname}/{zipname}.zip', compression=compress_param, index=False)

    @staticmethod
    def import_module(fpath: str):
        """Import module to a variable from a specific filepath."""
        module_name = fpath.split('/')[-1]
        module_dir = re.sub(module_name, '', fpath)
        spec = importlib.util.spec_from_file_location(module_name, f'{module_dir}{module_name}')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def create_yaml_template(
        input_fp: str,
        output_fp: str
    ) -> None:
        """Creates empty .yaml template from a .yaml file.

        Useful for converting a filled out environment .yaml file into an empty template for users
        to clone into their directories without seeing anyone else's secrets.
        
        Parameters
        ----------
        input_fp : str
            Filepath to the input .yaml file.
        output_fp : str
            Output filepath of the empty .yaml template.
        """
        with open(input_fp, encoding='utf-8') as file:
            env = file.readlines()

        template = []
        for line in env:
            if line == '\n':
                template.append('\n')
            elif re.search('#', line):
                template.append(line)
            elif not re.search(':', line):
                continue
            else:
                if re.search('\[', line):
                    line = re.sub(':.+', ': []', line)
                else:
                    line = re.sub(':.+', ':', line)
                template.append(line)

        with open(output_fp, 'w', encoding='utf-8') as f:
            f.write(''.join(template))

    @staticmethod
    def run_shell(cmd: str) -> None:
        """Wrapper around shell command to raise specific error message."""
        output = subprocess.run(cmd, shell=True, capture_output=True)
        if output.returncode != 0:
            raise RuntimeError(f"{output.stderr.decode('utf-8')}")

    class HidePrints:
        """Suppress print statements.
        
        Example use:

        import HidePrints

        def func_with_prints():
            print('jaja')

        with HidePrints():
            # This will not print 'jaja'.
            func_with_prints()
        """
        def __enter__(self):
            self._original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w', encoding='utf-8')

        def __exit__(self, exc_type, exc_val, exc_tb):
            sys.stdout.close()
            sys.stdout = self._original_stdout

    @staticmethod
    def read_files(
        dirname: str,
        filetype: Literal['csv', 'ftr'] = 'csv',
        period_beg: Optional[Union[str, pd.Timestamp]] = None,
        period_end: Optional[Union[str, pd.Timestamp]] = None,
        add_date: bool = False,
        add_filename: bool = False
    )-> pd.DataFrame:
        """Read in a directory of files as a dataframe.

        Parameters
        ----------
        dirname : str
            Directory where all files to be read are located.
        filetype : Literal[&#39;csv&#39;, &#39;ftr&#39;], optional, default 'csv'
        period_beg : Union[str, pd.Timestamp], optional, default False
            Given that each filename contains a date in the format of
            'YYYYmmdd', filter out files with date before period_beg.
            Note that period_beg will be normalized to 00:00:00.
        period_end : Union[str, pd.Timestamp], optional, default False
            Given that each filename contains a date in the format of
            'YYYYmmdd', filter out files with date after period_end.            
            Note that period_end will be normalized to 00:00:00.
        add_date : bool, optional, default False
            Given that each filename contains a date in the format of
            'YYYYmmdd', append a column named `_file_created_at` with
            extracted date from filename.
        add_filename: bool, optional, default False
            Append a column named `_file_name` with extracted filenames.
        """
        if dirname[-1] == '/':
            dirname = dirname[:-1]
        if period_beg:
            period_beg = pd.Timestamp(period_beg).normalize()
        if period_end:
            period_end = pd.Timestamp(period_end).normalize()

        files = []
        fpaths = glob.glob(f'{dirname}/*{filetype}')
        if not fpaths:
            raise TypeError('No files found in specified directory.')

        for fpath in sorted(fpaths, reverse=True):
            if filetype == 'csv':
                file = pd.read_csv(fpath)
            elif filetype == 'ftr':
                file = pd.read_feather(fpath)
            else:
                raise ValueError('Unsupported file_type.')

            fname = fpath.split('/')[-1]
            file_date = re.search('\d{8}', fname).group()
            file_date = pd.Timestamp(file_date).normalize()
            
            if period_beg and period_beg > file_date:
                continue
            if period_end and period_end < file_date:
                continue
    
            if add_date:
                filedate_col = '_file_created_at'
                if filedate_col in file.columns:
                    raise ValueError(f'`{filedate_col}` column already exists.')
                file[filedate_col] = file_date

            if add_filename:
                filename_col = '_file_name'
                if filename_col in file.columns:
                    raise ValueError(f'`{filename_col}` column already exists.')
                file[filename_col] = fname
            files.append(file)
        files = pd.concat(files, axis=0, ignore_index=True)
        return files

    @staticmethod
    def snake_to_pascal(str_: str) -> str:
        return ''.join([_snake.capitalize() for _snake in str_.split('_')])
