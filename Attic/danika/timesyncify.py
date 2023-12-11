import os
import csv
import argparse
import itertools
import configparser
from copy import copy
from dataclasses import dataclass
from datetime import datetime as dt
from functools import partial, reduce, wraps
from typing import List, Tuple, Optional, Any, Callable

import s3fs
import tqdm
import dask
import boto3
import fsspec
import numpy as np
import pandas as pd
import pystac_client
import rasterio as rio
from dask.distributed import Client, as_completed, worker_client
from dask_kubernetes.classic import KubeCluster
from fsspec.implementations.local import LocalFileSystem

Affine = Tuple[float, float, float, float, float, float]

QA_FILL = 0
QA_CLEAR = 6
QA_WATER = 7


@dataclass(frozen=True)
class Bounds:
    """
    Class to hold spatial coordinate bounds
    """
    min_x: float
    max_x: float
    min_y: float
    max_y: float


class StacRecord:
    """
    Class with methods for parsing STAC records
    """

    @staticmethod
    def sensor(record: dict) -> str:
        """
        Parse the sensor shorthand abbreviation at the beginning of the observation id
        """
        return record['id'].split('_')[0]

    @staticmethod
    def hv(record: dict) -> str:
        """
        Retrieve the tile coordinates as a string patterned like hhvv
        """
        return record['properties']['landsat:grid_horizontal'] + record['properties']['landsat:grid_vertical']

    @staticmethod
    def date(record: dict) -> str:
        """
        Retrieve the datetime string
        """
        return record['properties']['datetime']

    @staticmethod
    def year(record: dict) -> int:
        """
        Retrieve the observation year
        Note: Do not try to use '%Y-%m-%dT%H:%M:%S.%fZ' as the format code, it will not work
            because the microseconds are not always six digits
        """
        date = record['properties']['datetime']
        return dt.strptime(date.split('.')[0], '%Y-%m-%dT%H:%M:%S').year

    @staticmethod
    def doy(record: dict) -> int:
        """
        Retrieve the observation DOY
        Note: Do not try to use '%Y-%m-%dT%H:%M:%S.%fZ' as the format code, it will not work
            because the microseconds are not always six digits
        """
        date = record['properties']['datetime']
        return dt.strptime(date.split('.')[0], '%Y-%m-%dT%H:%M:%S').timetuple().tm_yday

    @staticmethod
    def year_doy(record: dict) -> str:
        """
        Retrieve a formatted year/doy string
        """
        return f'{StacRecord.year(record)}_{StacRecord.doy(record):03}'

    @staticmethod
    def asset_href(record: dict, band: str) -> str:
        """
        Retrieve the s3 location of a STAC asset
        """
        return record['assets'][band]['alternate']['s3']['href']

    @staticmethod
    def crs(record: dict) -> str:
        """
        Retrieve the coordinate reference system from a STAC record as WKT
        """
        return record['properties']['proj:wkt2']


def timesync_band_list() -> List[str]:
    """
    Get the bands relevant to TimeSync data retrieval
    """
    return ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22', 'qa_pixel']


def centered_window(x: float, y: float, width: int, height: int, ds: rio.io.DatasetReader) -> rio.windows.Window:
    """
    Create a window centered on the x, y of a pixel of interest
    Width and height are in pixels
    """
    row_offset, col_offset = ds.index(x, y)
    return rio.windows.Window(
        col_offset - (width // 2),
        row_offset - (height // 2),
        width,
        height)


def centered_bounds(x: float, y: float, width: int, height: int, pixel_size: int = 30):
    """
    Create coordinate bounds centered on an x/y coordinate
    """
    return Bounds(
        min_x=x - ((width // 2) * pixel_size),
        max_x=x + ((width // 2) * pixel_size),
        min_y=y - ((height // 2) * pixel_size),
        max_y=y + ((height // 2) * pixel_size))


def single_pixel_window(x: float, y: float, ds: rio.io.DatasetReader) -> rio.windows.Window:
    """
    Get a window representing a single pixel
    """
    row_offset, col_offset = ds.index(x, y)
    return rio.windows.Window(col_offset, row_offset, 1, 1)


def build_query(h: int, v: int, region: str = 'CU', collection: str = 'landsat-c2ard-sr',
                datetime: str = '1984-01/2022-12-31', limit: Optional[int] = None) -> dict:
    """
    Construct a STAC query based on h/v tile coordinates
    """
    return {
        'collections': collection,
        'datetime': datetime,
        'limit': limit,
        'query': {'landsat:grid_horizontal': {'eq': f'{h:02}'},
                  'landsat:grid_vertical': {'eq': f'{v:02}'},
                  'landsat:grid_region': {'eq': region}}}


def tile_grid_affine(region: str) -> Affine:
    """
    Get the ARD tile grid affine based on the regional code
    """
    return {
        'CU': (-2565585, 150000, 0, 3314805, 0, -150000),  # CONUS
    }[region]


def transform_geo(x: float, y: float, affine: Affine) -> Tuple[int, int]:
    """
    Perform the affine transformation from an x/y coordinate to row/col space.
    """
    col = (x - affine[0] - affine[3] * affine[2]) / affine[1]
    row = (y - affine[3] - affine[0] * affine[4]) / affine[5]
    return int(col), int(row)


def determine_hv(x: float, y: float, region: str) -> Tuple[int, int]:
    """
    Determine the ARD tile (in h/v coordinates) containing the x/y coordinate
    """
    h, v = transform_geo(x, y, tile_grid_affine(region))
    return h, v


def determine_hvs(bbox, region: str) -> itertools.product:
    """
    Determine the h/v coordinates of tiles that intersect a bounding box
    """
    min_h, min_v = determine_hv(bbox.min_x, bbox.max_y, region)
    max_h, max_v = determine_hv(bbox.max_x, bbox.min_y, region)
    return itertools.product(range(min_h, max_h + 1), range(min_v, max_v + 1))


def query_stac(query_params: dict) -> dict:
    """
    Query the STAC catalog using the provided query parameters
    """
    stac = pystac_client.Client.open('https://landsatlook.usgs.gov/stac-server')
    # This returns a dictionary with two keys, 'type' and 'features'
    results = stac.search(**query_params).item_collection_as_dict()
    # 'type' only contains the value 'FeatureCollection'; we care about what is in 'features'
    return results['features']


def group_dicts(records: List[dict], key_func: Callable) -> itertools.groupby:
    """
    Group a list of dictionaries based on key value
    """
    records = sorted(records, key=key_func)
    return itertools.groupby(records, key=key_func)


def convert_sr(data: np.ndarray) -> np.ndarray:
    """
    Re-scale Landsat Collection 2 spectral data values back to the Collection 1 range
    """
    return ((data.astype(float) * 0.0000275 - 0.2) * 10000).astype(np.int16)


def data_to_collection_1(old_dict: dict) -> dict:
    """
    Convert a dictionary of surface reflectance bands to the Landsat Collection 1 numerical range
    """
    new_dict = {}
    for key, value in old_dict.items():
        new_dict[key] = convert_sr(value)
    return new_dict


def read_bands(record: dict, bands: List[str], plot: Tuple[Any, ...], width: int, height: int) -> dict:
    """
    Read in an ROI for an observation in the STAC record for all bands
    """
    out = {}
    for band in bands:
        with rio.open(StacRecord.asset_href(record, band)) as ds:
            window = centered_window(plot.x, plot.y, width, height, ds)
            out[band] = ds.read(1, window=window, boundless=True, fill_value=0)
    return out


def read_qa_at_plot(record: dict, plot: Tuple[Any, ...]) -> int:
    """
    Read a single pixel at the plot location
    """
    with rio.open(StacRecord.asset_href(record, 'qa_pixel')) as ds:
        window = single_pixel_window(plot.x, plot.y, ds)
        out = ds.read(1, window=window, boundless=False)
    if out.size == 0:
        return 1  # Treat values outside the spatial extent as fill
    return out.item()


def add_bands(dict_a: dict, dict_b: dict) -> dict:
    """
    Combine two observation dictionaries by adding the values for each band
    """
    out = {}
    for band in dict_a:
        out[band] = dict_a[band] + dict_b[band]
    return out


def composite(data: dict, bands: List[str]) -> np.ndarray:
    """
    Create a multi-band ndarray from band names
    """
    return np.stack([data[band] for band in bands])


def tasseled_cap(data: dict) -> np.ndarray:
    """
    Create a composite of tasseled cap values
    """
    band_order = ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22']  # Must match coefficient order below
    arr = np.stack([data[band] for band in band_order], axis=2)
    b = np.tensordot(arr, [0.2043, 0.4158, 0.5524, 0.5741, 0.3124, 0.2303], axes=1)  # Brightness
    g = np.tensordot(arr, [-0.1603, -0.2819, -0.4934, 0.7940, -0.0002, -0.1446], axes=1)  # Greenness
    w = np.tensordot(arr, [0.0315, 0.2021, 0.3102, 0.1594, -0.6806, -0.6109], axes=1)  # Wetness
    return np.stack([b, g, w])


def build_affine(x_off: float, y_off: float, x_size: float = 30, y_size: float = 30, x_shear: float = 0,
                 y_shear: float = 0) -> rio.Affine:
    """
    Build the affine tuple in the rasterio format (different from GDAL)
    """
    return rio.Affine(x_size, x_shear, x_off, y_shear, y_size, -y_off)


def write_to_png(file: str, array: np.ndarray, crs: str, transform: rio.Affine) -> None:
    """
    Write a PNG file as three 8-bit channels
    """
    profile = {
        'driver': 'PNG',
        'count': 3,
        'nodata': None,
        'crs': crs,
        'transform': transform,
        'height': array.shape[1],
        'width': array.shape[2],
        'dtype': np.uint8}

    with rio.open(file, mode='w', **profile) as ds:
        ds.write(array)


def byte_scale(array: np.ndarray, min_value: float, max_value: float) -> np.ndarray:
    """
    Scale the data between min_value and max_value to 0-255
    """
    out_array = (255 / (max_value - min_value)) * (array - min_value)
    out_array = np.minimum(out_array, 255)
    out_array = np.maximum(out_array, 0)
    return out_array.astype(np.uint8)


def byte_scale_bands(array: np.ndarray, all_bounds: List[Tuple[int, int]], axis: int = 0) -> np.ndarray:
    """
    Convert a multi-band array to scaled 8-bit
    """
    out = []
    for i, (min_value, max_value) in enumerate(all_bounds):
        out.append(byte_scale(array.take(i, axis=axis), min_value, max_value))
    return np.stack(out, axis=axis)


def center(array: np.ndarray) -> Tuple[int, ...]:
    """
    Get the indices for the center of an array
    """
    return tuple(x // 2 for x in array.shape)


def center_value(array: np.ndarray) -> int:
    """
    Get the center value of an array
    """
    return array[center(array)]


def spectral_data(data: dict) -> dict:
    """
    Get the data for the center pixel in the chip
    """
    return {band: center_value(array) for band, array in data.items()}


def df_to_csv(df: pd.DataFrame, params: dict, output: dict) -> None:
    """
    Write the dataframe to the csv file
    """
    with params['fs'].open(output['scsv'], 'w') as f:
        df.to_csv(f, index=False)


def classify_qa(qa: int) -> int:
    """
    Return a value indicating the pixel is clear/water (0) or fill/cloud (1)
    """
    if passes_qa_check(qa, enable_cloud_filtering=True):
        return 0
    return 1


def build_df(pixel_data: dict, record: dict, project_id: str, plot_id: str) -> pd.DataFrame:
    """
    Build the output dataframe
    """
    return pd.DataFrame({
        'sensor': StacRecord.sensor(record),
        'project_id': project_id,
        'plot_id': plot_id,
        'hv': StacRecord.hv(record),
        'year': StacRecord.year(record),
        'doy': StacRecord.doy(record),
        'blue': pixel_data['blue'],
        'green': pixel_data['green'],
        'red': pixel_data['red'],
        'nir': pixel_data['nir08'],
        'swir1': pixel_data['swir16'],
        'swir2': pixel_data['swir22'],
        'qa': classify_qa(pixel_data['qa_pixel']),
        'data': StacRecord.date(record)}, index=[0])


def invalid_pixel() -> dict:
    """
    Get band values to represent and invalid pixel
    """
    return {
        'blue': 0,
        'green': 0,
        'red': 0,
        'nir08': 0,
        'swir16': 0,
        'swir22': 0,
        'qa_pixel': 1}


def adjust_for_s3(in_dict, filesystem) -> dict:
    """
    Adjust the output file names to use the /vsis3/ file system handler for image data
    """
    out_dict = copy(in_dict)
    if isinstance(filesystem, s3fs.core.S3FileSystem):
        for key in in_dict:
            if in_dict[key].endswith('.png') or in_dict[key].endswith('.tif'):
                out_dict[key] = in_dict[key].replace('s3:/', '/vsis3')
    return out_dict


def process_group(group: List[dict], plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process a group of STAC records associated with a plot into output PNGs
    """
    with rio.Env(rio.session.AWSSession(boto3.Session(), requester_pays=True), AWS_NO_SIGN_REQUEST='NO'):

        # Set up the output filenames and (as applicable) directories
        output = adjust_for_s3(
            output_files(params['project_dir'], plot.project_id, plot.plot_id, StacRecord.year_doy(group[0])),
            params['fs'])
        for out in output.values():
            make_dirs(params['fs'], out)

        # Determine if the center pixel is fill
        if not any(passes_qa_check(read_qa_at_plot(record, plot)) for record in group):
            # Optionally, write an entry for an invalid pixel. This had been previous functionality,
            # but because TimeSync does not expect this entry, I am disabling it.
            # df_to_csv(build_df(invalid_pixel(), group[0], plot.project_id, plot.plot_id), params, output)
            return

        # Read and combine the data records
        data_stack = [
            read_bands(observation, timesync_band_list(), plot, params['chip_size'][0], params['chip_size'][1]) for
            observation in group]
        combined_data = data_to_collection_1(reduce(add_bands, data_stack))

    with rio.Env(**params['rio_env']):

        # Get geospatial attributes
        bounds = centered_bounds(plot.x, plot.y, params['chip_size'][0], params['chip_size'][1])
        aff = build_affine(bounds.min_x, bounds.max_y)
        crs = StacRecord.crs(group[0])

        # Calculate the output chip data
        output_tcap = tasseled_cap(combined_data)
        output_b743 = composite(combined_data, bands=['swir22', 'nir08', 'red'])
        output_b432 = composite(combined_data, bands=['nir08', 'red', 'green'])

        # Stretch the chip data and write to PNG
        write_to_png(output['tcap'], byte_scale_bands(output_tcap, [(604, 5592), (49, 3147), (-2245, 843)]), crs, aff)
        write_to_png(output['b743'], byte_scale_bands(output_b743, [(-904, 3696), (151, 4951), (-300, 2500)]), crs, aff)
        write_to_png(output['b432'], byte_scale_bands(output_b432, [(151, 4951), (-300, 2500), (50, 1150)]), crs, aff)

        # Define the metadata and spectral data for this observation and export to a csv
        df_to_csv(build_df(spectral_data(combined_data), group[0], plot.project_id, plot.plot_id), params, output)


def group_records(records: List[dict]) -> List[List[dict]]:
    """
    Group records based on the observation ID
    """
    out = []
    for _, group in group_dicts(records, StacRecord.year_doy):
        out.append(list(group))
    return out


def output_files(project_dir: str, project_id: str, plot_id: str, year_doy: str) -> dict:
    """
    Build the file names for the output files for TimeSync
    """
    return {
        'scsv': f'{project_dir}/prj_{project_id}/{plot_id}_spectral_files_set_{year_doy}.csv',
        'tcap': f'{project_dir}/prj_{project_id}/tc/plot_{plot_id}/plot_{plot_id}_{year_doy}.png',
        'b743': f'{project_dir}/prj_{project_id}/b743/plot_{plot_id}/plot_{plot_id}_{year_doy}.png',
        'b432': f'{project_dir}/prj_{project_id}/b432/plot_{plot_id}/plot_{plot_id}_{year_doy}.png'}


def report_status(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(plot: Tuple[Any, ...], *args, **kwargs) -> Tuple[Tuple[Any, ...], str]:
        """
        Return the plot and any exception raised, or report complete
        """
        try:
            func(plot, *args, **kwargs)
            return plot, 'complete'
        except Exception as error:
            return plot, str(error)

    return wrapper


@report_status
def process_plot(plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process an individual plot
    """
    groups = group_records(stac_records_for_plot(plot, params))
    for group in groups:
        process_group(group, plot, params)


@report_status
def process_plot_delayed(plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process an individual plot
    """
    groups = group_records(stac_records_for_plot(plot, params))
    func = partial(process_group, plot=plot, params=params)
    with worker_client() as client:
        futures = client.map(func, groups)
        _ = client.gather(futures)


def check_bit(value: int, bit: int) -> bool:
    """
    Check whether a bit is set
    """
    return bool((value & (1 << bit)))


def passes_qa_check(qa: int, enable_cloud_filtering=False) -> bool:
    """
    Make sure the QA value is not indicating fill and (optionally) ensure clear or water bits are set
    """
    if check_bit(qa, QA_FILL):
        return False
    if enable_cloud_filtering and not (check_bit(qa, QA_CLEAR) or check_bit(qa, QA_WATER)):
        return False
    return True


def make_dirs(fs, file: str) -> None:
    """
    Create parent directories if it makes sense to do so
    """
    if isinstance(fs, LocalFileSystem):
        fs.makedirs(os.path.dirname(file), exist_ok=True)


def stac_records_for_plot(plot: Tuple[Any, ...], params: dict) -> List[dict]:
    """
    Retrieve the stac records relevant for the plot
    """
    query_results = []
    roi = centered_bounds(plot.x, plot.y, params['chip_size'][0], params['chip_size'][1])
    for h, v in determine_hvs(roi, region=params['region']):
        query_results.extend(query_stac(build_query(h, v, region=params['region'])))
    return query_results


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


def aws_credentials(profile: str) -> Tuple[str, str]:
    """
    Fetch information on AWS credentials
    """
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.environ['HOME'], '.aws', 'credentials'))
    return parser[profile]['aws_access_key_id'], parser[profile]['aws_secret_access_key']


def local_setup(*args) -> dict:
    """
    Extra setup for writing output to a local file system
    """
    return {
        'fs': fsspec.filesystem('file'),
        'rio_env': {'session': None}}


def aws_setup(profile: str, *args) -> dict:
    """
    Extra setup for writing to an S3 bucket
    """
    key, secret = aws_credentials(profile)
    return {
        'fs': fsspec.filesystem('s3', key=key, secret=secret),
        'rio_env': {'session': rio.session.AWSSession(
            aws_access_key_id=key, aws_secret_access_key=secret),
            'CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE': 'YES'}}


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


def data_preparation(plot_file: str, log_file: str) -> Tuple[pd.DataFrame, int, int]:
    """
    Read in the plot geolocation information and prior processing history
    """
    # Read in the plot data
    plots_df = format_plot_data(plot_file)

    if os.path.exists(log_file) and (os.path.getsize(log_file) > 0):
        log_df = format_log_data(log_file)

        # Get the most recent status from any previous processing run
        df = plots_df.merge(
            log_df.drop_duplicates(subset='plot_id', keep='last'),
            how='left', on=['project_id', 'plot_id'])

    else:
        df = plots_df.copy().reindex(columns=plots_df.columns.tolist() + ['status'])

    n_total, n_completed = len(df), len(df[df.status == 'complete'])
    plots_to_process = df.loc[df.status != 'complete', plots_df.columns]

    return plots_to_process, n_completed, n_total


def process_on_kube(params: dict) -> None:
    """
    Process a group of plots on the CHS Pangeo Kubernetes cluster
    """
    # Get input data
    plots_df, n_completed, n_total = data_preparation(params['plot_file'], log_file_name(params))
    if n_completed == n_total:
        print(f'All {n_total} plots processed successfully! Exiting...')
        return

    with dask.config.set({"distributed.worker.resources.stac_queries": 1}):
        with KubeCluster() as cluster, Client(cluster) as client:
            # Get the tcp address from the user (out of desperation)
            # tcp_address = input('Enter the tcp address of the client (as NN.NN.NN.NNN:NNNNN):\n')
            # client = Client(f'tcp://{tcp_address}')

            # Set up the cluster and get the dashboard address
            print('Dashboard: https://pangeo.chs.usgs.gov' + client.dashboard_link)
            cluster.adapt(maximum=150)  # me nice

            # Define the processing function
            processing_func = partial(process_plot_delayed, params=params)

            # Iterate over the plots to set individual plot priorities
            # The idea is to favor completing individual plots and reduce the need to cache/requery STAC records
            futures = []
            for plot in plots_df.itertuples():
                futures.append(client.submit(processing_func, plot,
                                             priority=-int(plot.plot_id),
                                             resources={'stac_queries': 1}))

            # As results are completed, log completion and errors
            desc = 'Processing plots'
            for completed in tqdm.tqdm(as_completed(futures), desc=desc, initial=n_completed, total=n_total):
                plot, status = completed.result()
                log_plot_status(plot, status, log_file_name(params))


def log_file_name(params: dict) -> str:
    """
    Define the output log file
    """
    return os.path.splitext(params['plot_file'])[0] + '.log'


def process_on_local(params: dict) -> None:
    """
    Local single-threaded processing
    """
    # Get input data
    plots_df, n_completed, n_total = data_preparation(params['plot_file'], log_file_name(params))
    if n_completed == n_total:
        print(f'All {n_total} plots processed successfully! Exiting...')
        return

    # Define the processing function
    processing_func = partial(process_plot, params=params)

    # Iterate over the plots
    for plot in tqdm.tqdm(plots_df.itertuples(), desc='Processing plots', initial=n_completed, total=n_total):
        plot, status = processing_func(plot)
        log_plot_status(plot, status, log_file_name(params))


def arg_parser() -> argparse.ArgumentParser:
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Create TimeSync chip and spectral timeseries data',
        epilog='python timesyncify.py s3://chs-pangeo-data-bucket/dwellington/timesync '
               '/home/jovyan/data/plot_list.csv --profile=default')
    parser.add_argument('project_dir', help='Project directory or S3 bucket to write results')
    parser.add_argument('plot_file', help='CSV file with header/columns that include: project_id, plot_id, x, y')
    parser.add_argument('--region', help='ARD regional identifier', default='CU', choices=['CU'])
    parser.add_argument('--chip_size', help='Output image chip size', default=[255, 255], type=int, nargs=2,
                        metavar=('width', 'height'))
    parser.add_argument('--profile', help='AWS profile w/write credentials to project dir', default='default')
    parser.add_argument('--process_on', help='Processing environment', default='kube_cluster',
                        choices=['local', 'kube_cluster'])
    parser.add_argument('--store_on', help='File system for output data', default='aws_s3', choices=['local', 'aws_s3'])
    return parser


def timesync_data_extraction(project_dir: str, plot_file: str, region: str, chip_size: List[int], process_on: str,
                             store_on: str, profile: Optional[str] = None) -> None:
    """
    Run TimeSync data extraction
    """
    params = locals()

    storage = {
        'local': local_setup,
        'aws_s3': aws_setup,
    }[store_on]

    process = {
        'kube_cluster': process_on_kube,
        'local': process_on_local,
    }[process_on]

    params.update(storage(profile))
    process(params)


if __name__ == '__main__':
    cl_args = arg_parser().parse_args()
    timesync_data_extraction(**vars(cl_args))
