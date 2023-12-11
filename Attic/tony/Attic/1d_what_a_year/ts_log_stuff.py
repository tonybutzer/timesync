import os
import pandas as pd
from typing import List, Tuple, Optional, Any, Callable, Iterable




def format_plot_data(plot_file: str) -> pd.DataFrame:
    """
    Read in the csv file containing geospatial plot data
    """
    return pd.read_csv(
        plot_file,
        usecols=['project_id', 'plot_id', 'x', 'y'],
        dtype={'project_id': str, 'plot_id': str, 'x': int, 'y': int})


def format_log_data(log_file: str) -> pd.DataFrame:
    """
    Read in the csv file containing a record of previous run(s)
    """
    return pd.read_csv(
        log_file,
        usecols=['project_id', 'plot_id', 'time', 'status'],
        dtype={'project_id': str, 'plot_id': str, 'time': str, 'status': str})


def append_to_csv(entry: list, csv_file: str) -> None:
    """
    Append a line to a csv file
    """
    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(entry)


def log_plot_status(plot: Tuple[Any, ...], status: str, log_file: str) -> None:
    """
    Write plot status to a log file
    """
    if not os.path.exists(log_file) or not (os.path.getsize(log_file) > 0):
        append_to_csv(['project_id', 'plot_id', 'time', 'status'], log_file)
    append_to_csv([plot.project_id, plot.plot_id, dt.now(), status], log_file)


def log_file_name(plot_file):
    """
    Define the output log file
    """
    return os.path.splitext(plot_file)[0] + '.log'

