from dataclasses import dataclass
from datetime import datetime as dt




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


