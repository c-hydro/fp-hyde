"""
Library Features:

Name:          lib_default_conventions
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180703'
Version:       '1.0.0'
"""

#######################################################################################
# Library
# Nothing to do here
#######################################################################################

# -------------------------------------------------------------------------------------
# Set default definition of file
oFileConventions = dict(

    general={
        'Conventions': 'CF-1.7',
        'title': '',
        'institution': 'CIMA Research Foundation - www.cimafoundation.org',
        'web-site':	'',
        'source': '',
        'history': '',
        'references': 'http://cf-pcmdi.llnl.gov/ ; http://cf-pcmdi.llnl.gov/documents/cf-standard-names/',
        'comment': 'Author(s): Fabio Delogu',
        'email': 'fabio.delogu@cimafoundation.org',
        'project-info':	'',
        'algorithm': '',
    },

    geosystem={
        'epsg_code': 4326,
        'grid_mapping_name': 'latitude_longitude',
        'longitude_of_prime_meridian': 0.0,
        'semi_major_axis': 6378137.0,
        'inverse_flattening': 298.257223563,
    },

    georeference={
        'bounding_box': None,
        'ncols': None,
        'nrows': None,
        'xllcorner': None,
        'yllcorner': None,
        'cellsize': None,
        'nodata_value': None
    },

)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Set default definition of variable(s)
oVarConventions = dict(

    time={
        'long_name': 'time',
        'units': 'days since 1990-1-1 0:0:0',
        'calendar': None,
    },

    terrain={
        'long_name': 'geometric height',
        'standard_name': 'altitude',
        'grid_mapping': 'crs',
        'dims': {'X': 'west_east', 'Y': 'south_north'},
        'coordinates': 'longitude latitude',
        'cell_method': '',
        'units': 'm',
        'positive': 'up',
        'pressure_level': '',
        'ScaleFactor': 1,
        'Format': 'f4',
        'Missing_value': -9999.0,
        '_FillValue': None,
        'Valid_range': '',
        'description': '',
    },

    longitude={
        'long_name': 'longitude coordinate',
        'standard_name': 'longitude',
        'grid_mapping': '',
        'dims': {'X': 'west_east', 'Y': 'south_north'},
        'coordinates': '',
        'cell_method': '',
        'coordinate_reference_frame': 'urn:ogc:crs:EPSG::4326',
        'reference': 'WGS84',
        'units': 'degrees_east',
        'pressure_level': '',
        'ScaleFactor': 1,
        'Format': 'f4',
        'Missing_value': -9999.0,
        '_FillValue': None,
        'Valid_range': '-180, 180',
        'description': '',
    },

    latitude={
        'long_name': 'latitude coordinate',
        'standard_name': 'latitude',
        'grid_mapping': '',
        'dims': {'X': 'west_east', 'Y': 'south_north'},
        'coordinates': '',
        'cell_method': '',
        'coordinate_reference_frame': 'urn:ogc:crs:EPSG::4326',
        'reference': 'WGS84',
        'units': 'degrees_north',
        'pressure_level': '',
        'ScaleFactor': 1,
        'Format': 'f4',
        'Missing_value': -9999.0,
        '_FillValue': None,
        'Valid_range': '-90, 90',
        'description': '',
    },

    var2d={
        'long_name': '',
        'standard_name': '',
        'grid_mapping': 'crs',
        'dims': {'X': 'west_east', 'Y': 'south_north'},
        'coordinates': 'longitude latitude',
        'ancillary_variables': '',
        'cell_method': '',
        'units': '',
        'pressure_level': '',
        'ScaleFactor': 1,
        'Format': 'f4',
        'Missing_value': -9999.0,
        '_FillValue': None,
        'Valid_range': '',
        'flag_masks': '',
        'flag_values': '',
        'flag_meanings': '',
        'colormap': '',
        'description': '',
    },

    var3d={
        'long_name': '',
        'standard_name': '',
        'grid_mapping': 'crs',
        'dims': {'X': 'west_east', 'Y': 'south_north', 'Time': 'time'},
        'coordinates': 'longitude latitude',
        'ancillary_variables': '',
        'cell_method': '',
        'units': '',
        'pressure_level': '',
        'ScaleFactor': 1,
        'Format': 'f4',
        'Missing_value': -9999.0,
        '_FillValue': None,
        'Valid_range': '',
        'flag_masks': '',
        'flag_values': '',
        'flag_meanings': '',
        'colormap': '',
        'description': '',
    },

    var4d={
        'long_name': '',
        'standard_name': '',
        'grid_mapping': 'crs',
        'dims': {'level': 'pressure', 'X': 'west_east', 'Y': 'south_north', 'Time': 'time'},
        'coordinates': 'longitude latitude',
        'ancillary_variables': '',
        'cell_method': '',
        'units': '',
        'pressure_level': '',
        'ScaleFactor': 1,
        'Format': 'f4',
        'Missing_value': -9999.0,
        '_FillValue': None,
        'Valid_range': '',
        'flag_masks': '',
        'flag_values': '',
        'flag_meanings': '',
        'colormap': '',
        'description': '',
    }

)
# -------------------------------------------------------------------------------------
