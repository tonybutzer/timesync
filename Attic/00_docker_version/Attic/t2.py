import os
import rasterio as rio

os.environ['AWS_REQUEST_PAYER'] = 'requester'
os.environ['GDAL_DISABLE_READDIR_ON_OPEN']='EMPTY_DIR'
os.environ['GDAL_HTTP_MAX_RETRY']='10'
os.environ['GDAL_HTTP_RETRY_DELAY']='3'
os.environ['GDAL_PAM_ENABLED']='NO'


image = 's3://usgs-landsat-ard/collection02/tm/1995/CU/013/013/LT05_CU_013013_19950107_20210424_02/LT05_CU_013013_19950107_20210424_02_SR_B1.TIF'

width=256
height=256

with rio.open(image) as ds:
                    window = rio.windows.Window(0, 0, 256, 256)
                    #window = centered_window(0, 0, width, height, ds)
                    # Get a masked array and fill it to avoid a bug with gdal/rasterio
                    #out = ds.read(1, window=window, boundless=True, fill_value=0, masked=True).filled()
                    out = ds.read(1)
                    print(type(out))
                    print(out.shape)

                    out2 = ds.read(1, window=window)
                    print(type(out2))
                    print(out2.shape)

                    out3 = ds.read(1, window=window, fill_value=0, masked=True)
                    print(type(out3))
                    print(out3.shape)

                    out4 = ds.read(1, window=window, fill_value=0, masked=True).filled()
                    print(type(out4))
                    print(out4.shape)



