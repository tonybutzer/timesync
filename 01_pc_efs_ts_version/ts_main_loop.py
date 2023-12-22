#!/usr/bin/env python
# coding: utf-8

# Python AWS and GDAL BS
import sys, traceback
import os
import pickle
import boto3

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
from ts_process_group import get_the_outputs_list

from ts_log_stuff import format_plot_data, log_file_name

def create_directory(directory_path):
    # Check if the directory already exists
    if not os.path.exists(directory_path):
        # Create the directory and its parents if they don't exist
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")


def pickle_to_efs(the_object, filename):
    pickle_file_path = filename
    with open(pickle_file_path, 'wb') as pickle_file:
        pickle.dump(the_object, pickle_file)

    print(f"Data has been pickled and saved to '{pickle_file_path}'.")


def pickle_the_outputs(year, plot, the_outputs):
    print(plot)
    print(plot.plot_id)

    number_str = str(plot.plot_id).zfill(4)
    fn = f'/efs/timesync/{year}/audit/{year}_{number_str}_{plot.project_id}_outputs.p'
    dirn = f'/efs/timesync/{year}/audit/'
    create_directory(dirn)
    pickle_to_efs(the_outputs,fn)




def process_plot(year, plot: Tuple[Any, ...], params: dict) -> None:
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
        process_plot(year, plot, params)
        # save_qa_rejects(year, plot)
        the_outputs = get_the_outputs_list()
        # print(the_outputs)
        pickle_the_outputs(year, plot, the_outputs)
        print('\nSuccess tracking goes here')
  
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj), flush=True)
    traceback.print_exc(file=sys.stdout)

def timesync_data_extraction(project_dir, project_id, plot_id, region, chip_size, year, x, y):
    """
    Run TimeSync data extraction
    """
    try:
        process_on_local(project_dir, project_id, plot_id, region, chip_size, year, x, y)
    except:
        PrintException()


def run_timesync(plot_id, year, x, y, project_id):

    config_params = {
        #'project_dir': f's3://dev-nlcd-developer/timesync/{year}/', 
        'project_dir': f'/efs/timesync/{year}/', 
        'project_id': project_id,
        'plot_id': plot_id,
        'region': 'CU', 
        'chip_size': [255, 255],
        'year': year,
        'x': x,
        'y': y
    }

    timesync_data_extraction(**config_params)  # docker and the cluster will not need dask

