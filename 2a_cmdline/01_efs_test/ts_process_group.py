import os
import numpy as np
import itertools


import rasterio as rio
import pandas as pd
import pystac_client
import fsspec
import s3fs


from copy import copy
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any, Callable, Iterable
from functools import partial, reduce, wraps


from fsspec.implementations.local import LocalFileSystem

from ts_stac_cog import StacRecord

Affine = Tuple[float, float, float, float, float, float]

# Constants
QA_FILL = 0
QA_CLEAR = 6
QA_WATER = 7
CONCURRENT_STAC_QUERIES = 2  # Prevents workers from consuming too much memory
LANDSAT_ARD_C2_FILL_VALUE = 0

# QA Rejects dates list

QA_Rejects = []

def get_qa_rejects_list():
    global QA_Rejects
    return QA_Rejects


# This AWS stuff could likely be simplified more to come ... -tony

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

def output_files(project_dir: str, project_id: str, plot_id: str, year_doy: str) -> dict:
    """
    Build the file names for the output files for TimeSync
    """
    return {
        'scsv': os.path.join(project_dir, f'prj_{project_id}/{plot_id}_spectral_files_set_{year_doy}.csv'),
        'tcap': os.path.join(project_dir, f'prj_{project_id}/tc/plot_{plot_id}/plot_{plot_id}_{year_doy}.png'),
        'b743': os.path.join(project_dir, f'prj_{project_id}/b743/plot_{plot_id}/plot_{plot_id}_{year_doy}.png'),
        'b432': os.path.join(project_dir, f'prj_{project_id}/b432/plot_{plot_id}/plot_{plot_id}_{year_doy}.png')}


@dataclass(frozen=True)
class Bounds:
    """
    Class to hold spatial coordinate bounds
    """
    min_x: float
    max_x: float
    min_y: float
    max_y: float


def timesync_band_list() -> List[str]:
    """
    Get the bands relevant to TimeSync data retrieval
    """
    return ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22', 'qa_pixel']


def landsat_optical_band_list() -> List[str]:
    """
    Get the optical wavelength Landsat bands
    """
    return ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22']


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


def data_to_collection_1(old_dict: dict, bands: List[str]) -> dict:
    """
    Convert a dictionary of surface reflectance bands to the Landsat Collection 1 numerical range
    """
    new_dict = old_dict.copy()
    for key in bands:
        new_dict[key] = convert_sr(old_dict[key])
    return new_dict


def read_bands(record: dict, bands: List[str], plot: Tuple[Any, ...], width: int, height: int) -> dict:
    """
    Read in an ROI for an observation in the STAC record for all bands
    """
    out = {}
    for band in bands:
        cnt=20
        sleep=6
        while(cnt>0):
            try:
                with rio.open(StacRecord.asset_href(record, band)) as ds:
                    window = centered_window(plot.x, plot.y, width, height, ds)
                    # Get a masked array and fill it to avoid a bug with gdal/rasterio
                    out[band] = ds.read(1, window=window, boundless=True, fill_value=0, masked=True).filled()
                    print('.',end='', flush=True)
                    break
            except rasterio.errors.RasterioIOError:
                print("Failure Failure Unexpected error:", sys.exc_info()[0])
                print('oops',cnt)
                s3_file_name = StacRecord.asset_href(record, band)
                print('oops',s3_file_name, flush=True)
                cnt = cnt - 1
                sleep(sleeptime)
    return out


def read_qa_at_plot(record: dict, plot: Tuple[Any, ...]) -> int:
    """
    Read a single pixel at the plot location
    """
    cnt=20
    sleep=6
    while(cnt>0):
        try:
            with rio.open(StacRecord.asset_href(record, 'qa_pixel')) as ds:
                window = single_pixel_window(plot.x, plot.y, ds)
                out = ds.read(1, window=window, boundless=False)
                break
        except rasterio.errors.RasterioIOError:
            print("Failure Failure QA PIXEL Unexpected error:", sys.exc_info()[0])
            print('oops',cnt)
            s3_file_name = StacRecord.asset_href(record, 'qa_pixel')
            print('oops',s3_file_name, flush=True)
            cnt = cnt - 1
            sleep(sleeptime)

            
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


def composite(data: dict, bands: List[str], axis: int = 0) -> np.ndarray:
    """
    Create a multi-band ndarray from band names
    """
    return np.stack([data[band] for band in bands], axis=axis)


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
    return rio.Affine(x_size, x_shear, x_off, y_shear, -y_size, y_off)


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

    try:
        with rio.open(file, mode='w', **profile) as ds:
            ds.write(array)
    except:
        print('Failure Failure writing PNG file', flush=True)


def array_mask(array: np.ndarray, value_to_mask = None, axis: int = 0) -> np.ndarray:
    """
    Boolean mask where the array matches the provided value anywhere along an axis
    """
    return (array == value_to_mask).any(axis=axis)


def apply_mask(array: np.ndarray, mask_array: np.ndarray, mask_value: float) -> np.ndarray:
    """
    Apply a Boolean mask 
    """
    arr = array.copy()
    arr[mask_array] = mask_value
    return arr


def byte_scale(array: np.ndarray, min_value: float, max_value: float) -> np.ndarray:
    """
    Scale the data between min_value and max_value to 0-255
    """
    out_array = (255 / (max_value - min_value)) * (array - min_value)
    out_array = np.minimum(out_array, 255)
    out_array = np.maximum(out_array, 0)
    return out_array.astype(np.uint8)


def byte_scale_bands(array: np.ndarray, all_bounds: List[Tuple[int, int]], 
                     mask: Optional[np.ndarray] = None, axis: int = 0) -> np.ndarray:
    """
    Convert a multi-band array to scaled 8-bit
    Masked values are set to 0
    """
    out = []
    for i, (min_value, max_value) in enumerate(all_bounds):
        byte_image = byte_scale(array.take(i, axis=axis), min_value, max_value)
        out.append(apply_mask(byte_image, mask, mask_value=0))
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
    #fs = fsspec.filesystem('s3', anon=False, requester_pays=True)
    fs = fsspec.filesystem('file')

    with fs.open(output['scsv'], 'w') as f:
        df.to_csv(f, index=False)


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
        'date': StacRecord.date(record)}, index=[0])


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

def build_query(h: int, v: int, region: str = 'CU', collection: str = 'landsat-c2ard-sr',
                datetime: str = '1984-01/1985-12-31', limit: Optional[int] = None) -> dict:
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

def group_records(records: List[dict]) -> List[List[dict]]:
    """
    Group records based on the observation ID
    """
    out = []
    for _, group in group_dicts(records, StacRecord.year_doy):
        out.append(list(group))
    return out

def stac_records_for_plot(plot: Tuple[Any, ...], params: dict) -> List[dict]:
    """
    Retrieve the stac records relevant for the plot
    """
    query_results = []
    roi = centered_bounds(plot.x, plot.y, params['chip_size'][0], params['chip_size'][1])
    my_year = params['year']
    my_dates = f'{my_year}-01-01/{my_year}-12-01'
    for h, v in determine_hvs(roi, region=params['region']):
        query_results.extend(query_stac(build_query(h, v, region=params['region'], datetime=my_dates)))
    return query_results

def make_dirs(fs, file: str) -> None:
    """
    Create parent directories if it makes sense to do so
    """
    if isinstance(fs, LocalFileSystem):
        fs.makedirs(os.path.dirname(file), exist_ok=True)


def process_group(group: List[dict], plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process a group of STAC records associated with a plot into output PNGs
    """
    global QA_Rejects
    #fs = fsspec.filesystem('s3', anon=False, requester_pays=True)
    fs = fsspec.filesystem('file')

    # Set up the output filenames and (as applicable) directories
    output = adjust_for_s3(
        output_files(params['project_dir'], plot.project_id, plot.plot_id, StacRecord.year_doy(group[0])),
        fs)
    for out in output.values():
        make_dirs(fs, out)

    # Determine if the center pixel is fill
    if not any(passes_qa_check(read_qa_at_plot(record, plot)) for record in group):
        # Optionally, write an entry for an invalid pixel. This had been previous functionality,
        # but because TimeSync does not expect this entry, I am disabling it.
        # df_to_csv(build_df(invalid_pixel(), group[0], plot.project_id, plot.plot_id), params, output)
        for record in group:
            print('Failed qa:', record['properties']['datetime'])
            QA_Rejects.append(record['properties']['datetime'])
        return

    # Read and combine the data records
    data_stack = [
        read_bands(observation, timesync_band_list(), plot, params['chip_size'][0], params['chip_size'][1]) for
        observation in group]
    combined_data = data_to_collection_1(reduce(add_bands, data_stack), landsat_optical_band_list())


    # Get geospatial attributes
    bounds = centered_bounds(plot.x, plot.y, params['chip_size'][0], params['chip_size'][1])
    aff = build_affine(bounds.min_x, bounds.max_y)
    crs = StacRecord.crs(group[0])

    # Mask for fill values
    fill_value = convert_sr(np.array(LANDSAT_ARD_C2_FILL_VALUE))
    mask = array_mask(composite(combined_data, landsat_optical_band_list()), fill_value)

    # Calculate the output chip data
    output_tcap = tasseled_cap(combined_data)
    output_b743 = composite(combined_data, bands=['swir22', 'nir08', 'red'])
    output_b432 = composite(combined_data, bands=['nir08', 'red', 'green'])

    # Stretch the chip data and write to PNG
    write_to_png(output['tcap'], byte_scale_bands(output_tcap, [(604, 5592), (49, 3147), (-2245, 843)], mask), crs, aff)
    write_to_png(output['b743'], byte_scale_bands(output_b743, [(-904, 3696), (151, 4951), (-300, 2500)], mask), crs, aff)
    write_to_png(output['b432'], byte_scale_bands(output_b432, [(151, 4951), (-300, 2500), (50, 1150)], mask), crs, aff)

    # Define the metadata and spectral data for this observation and export to a csv
    df_to_csv(build_df(spectral_data(combined_data), group[0], plot.project_id, plot.plot_id), params, output)

