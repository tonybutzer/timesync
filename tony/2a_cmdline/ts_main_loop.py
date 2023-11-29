#!/usr/bin/env python
# coding: utf-8

# Python AWS and GDAL BS
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
from ts_process_group import get_qa_rejects_list

from ts_log_stuff import format_plot_data, log_file_name

def pickle_to_s3(the_object, the_key):
    bucket='dev-nlcd-developer'
    #key='your_pickle_filename.pkl'
    key=the_key
    pickle_byte_obj = pickle.dumps(the_object)
    s3_resource = boto3.resource('s3')
    s3_resource.Object(bucket,key).put(Body=pickle_byte_obj)
    print('Writing pickle:', bucket, key)

def pickle_groups(year, plot, groups):
    print(plot)
    print(plot.plot_id)

    number_str = str(plot.plot_id).zfill(4)
    fn = f'timesync/{year}/audit/{year}_{number_str}_{plot.project_id}.p'

    bucket='dev-nlcd-developer'
    #key='your_pickle_filename.pkl'
    key=fn
    pickle_to_s3(groups, key)

    # pickle_byte_obj = pickle.dumps(groups)
    # s3_resource = boto3.resource('s3')
    # s3_resource.Object(bucket,key).put(Body=pickle_byte_obj)
    # print('Writing pickle:', bucket, key)


def process_plot(year, plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process an individual plot
    """
    print('called process_plot')
    groups = group_records(stac_records_for_plot(plot, params))
    pickle_groups(year, plot,groups)
    for group in groups:
        process_group(group, plot, params)

def save_qa_rejects(year,plot):

    number_str = str(plot.plot_id).zfill(4)
    fn = f'timesync/{year}/audit/{year}_{number_str}_{plot.project_id}_qa_rejects.p'

    qa_rejects = get_qa_rejects_list()

    bucket='dev-nlcd-developer'
    #key='your_pickle_filename.pkl'
    key=fn
    pickle_to_s3(qa_rejects, key)


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
        save_qa_rejects(year, plot)
        print('Success tracking goes here')
  


def timesync_data_extraction(project_dir, project_id, plot_id, region, chip_size, year, x, y):
    """
    Run TimeSync data extraction
    """
    process_on_local(project_dir, project_id, plot_id, region, chip_size, year, x, y)


def run_timesync(plot_id, year, x, y, project_id):

    config_params = {
        'project_dir': f's3://dev-nlcd-developer/timesync/{year}/', 
        'project_id': project_id,
        'plot_id': plot_id,
        'region': 'CU', 
        'chip_size': [255, 255],
        'year': year,
        'x': x,
        'y': y
    }

    timesync_data_extraction(**config_params)  # docker and the cluster will not need dask

