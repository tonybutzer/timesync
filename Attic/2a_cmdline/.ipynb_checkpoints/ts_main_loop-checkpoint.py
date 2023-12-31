#!/usr/bin/env python
# coding: utf-8

# Python AWS and GDAL BS
import os

os.environ['AWS_REQUEST_PAYER'] = 'requester'
os.environ['GDAL_DISABLE_READDIR_ON_OPEN']='EMPTY_DIR'
os.environ['GDAL_HTTP_MAX_RETRY']='10'
os.environ['GDAL_HTTP_RETRY_DELAY']='3'
os.environ['GDAL_PAM_ENABLED']='NO'


from functools import partial, reduce, wraps
from typing import List, Tuple, Optional, Any, Callable, Iterable

import pandas as pd

from ts_process_group import stac_records_for_plot, group_records
from ts_process_group import process_group

from ts_log_stuff import format_plot_data, log_file_name

def process_plot(plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process an individual plot
    """
    print('called process_plot')
    groups = group_records(stac_records_for_plot(plot, params))
    for group in groups:
        process_group(group, plot, params)


def process_on_local(project_dir, project_id, plot_id, region, chip_size, year, x, y):
    """
    Local single-threaded processing
    """
        
    plot_file=f'fake_plot_file_{project_id}_plot{plot_id}.csv'
    params = {
        'project_dir': project_dir, 
        'plot_file': plot_file, 
        'region': region, 
        'chip_size': chip_size,
        'year': year
    }

    # make plot df for legacy expectations Kelcy and Code code.
    
    plot_l = []
    plot_d = {
            'project_id': project_id,
            'plot_id': plot_id,
            'x': x,
            'y':y
            }
    plot_l.append(plot_d)

    plots_df = pd.DataFrame(plot_l)  # plots is misnomer - only one defined by x and y
    for plot in plots_df.itertuples():
        print(plot)
        process_plot(plot, params)
        print('Success tracking goes here')
  


def timesync_data_extraction(project_dir, project_id, plot_id, region, chip_size, year, x, y):
    """
    Run TimeSync data extraction
    """
    process_on_local(project_dir, project_id, plot_id, region, chip_size, year, x, y)


def run_timesync(plot_id, year, x, y, project_id):

    config_params = {
        'project_dir': f's3://dev-nlcd-developer/timesync/{project_id}/', 
        'project_id': project_id,
        'plot_id': plot_id,
        'region': 'CU', 
        'chip_size': [255, 255],
        'year': year,
        'x': x,
        'y': y
    }

    timesync_data_extraction(**config_params)  # docker and the cluster will not need dask

