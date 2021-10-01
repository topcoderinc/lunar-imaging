#!/usr/bin/env python3
import shutil
import pathlib
import os
import pandas as pd
import kalasiris as isis
from pathlib import Path

import pvl

## constants used by the tool
DELETE_INTERMEDIATE_FILES = True

# isis configuration
grid_definition = './config/grid_750.def'
pointreg_template = './config/pointreg_00.def'
#pointreg_template_2 = './config/pointreg_autoreg_00.def'
#pointreg_template_3 = './config/pointreg_medchip_00.def'
QL_THRESHOLD = 0.5
QL_THRESHOLD_ADV = 0.7
MODIFIED_ZSCORE_THRESH = 3.

# advanced coreg
scale = 20
coreg_config = './config.adv/coreg.maxcor_x20_0.6_40-80_250-500.def'
transform = 'translate'  # 'wrap'

# missions
lunar_missions_acronyms = ['apollo15', 'apollo16', 'apollo17', 'chandrayaan1', 'clementine1', 'kaguya', 'lo', 'lro', 'smart1']

# image formats
apollo_metric_file_types = ['.lbl', '.LBL', '.cub', '.CUB']
apollo_pan_file_types = ['.jp2', '.JP2', '.cub', '.CUB']
lo_file_types = ['.img', '.IMG', '.cub', ', .CUB']  #'.lbl', '.LBL',
lroc_file_types = ['.img', '.IMG', '.cub', '.CUB']

# isis parameters
isis_linc = 15  # The accuracy of camstats in the line direction (larger is less accurate)
isis_sinc = 15  # The accuracy of camstats in the sample direction (larger is less accurate)
isis_sinc_foot = 15  # The accuracy of the footprint in the sample direction (larger is less accurate)
isis_linc_foot = 15  # The accuracy of the footprint in the sample direction (larger is less accurate)

apollo_pan_csv = {
    'apollo15': 'AS15_Pancam_SV.csv',
    'apollo16': 'AS16_Pancam_SV.csv',
    'apollo17': 'AS17_Pancam_SV.csv',
}


class MetadataError(Exception):
    """Exception raised for metadata errors.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


def make_empty_folder(path):
    """Creates an empty folder, deleting anything there already"""
    shutil.rmtree(path, ignore_errors=True)
    pathlib.Path(path).mkdir(exist_ok=True)


def filename_frompath_noext(file_path):
    """Return the file name without extension"""
    #file_name = os.path.basename(file_path)
    #file_name_noext = os.path.splitext(file_name)[0]
    return Path(file_path).stem  # file_name_noext


def delete_files_with_ckeck(file_lst, output_folder):
    if DELETE_INTERMEDIATE_FILES:
        output_folder = pathlib.Path(output_folder)
        for file in file_lst:
            file = pathlib.Path(file)
            if file.exists() and output_folder.samefile(file.parent):
                file.unlink()


def str_to_tuple(tuple_str):
    """ Convert "(a, b)" string to tuple (a, b) """
    return tuple(tuple_str.strip('() ').split(','))


def get_stats_filename(artifacts_prefix, template=pointreg_template, index=None):
    """ Return filename with co-registration statistics """
    filename = f'{artifacts_prefix}_{Path(template).stem}'

    if index:
        filename = f'{filename}.stats_{index}.csv'
    else:
        filename = f'{filename}.stats.csv'

    return filename


def get_apollo_pan_params(image_name_wo_ext, mission):
    """ Get parameters for specific Apollo panoramic image """
    pan_params = pd.read_csv(apollo_pan_csv[mission])
    #utc_time, nadir_point(lat, lon), spacecraft_altitude, camera_axis_intersect(lon, lat)
    pan_params = pan_params[['image_name', 'utc_time', 'nadir_point', 'spacecraft_altitude', 'camera_axis_intersect']]
    param_dict = pan_params[pan_params['image_name'] == str(image_name_wo_ext).upper()].iloc[0].to_dict()

    param_dict['gmt'] = param_dict['utc_time'] #'"' + param_dict['utc_time'] + '"'
    param_dict['lat_nadir'], param_dict['lon_nadir'] = str_to_tuple(param_dict['nadir_point'])
    # order of (lat, lon) in tuple is different here - it's not a bug
    param_dict['lon_int'], param_dict['lat_int'] = str_to_tuple(param_dict['camera_axis_intersect'])
    # constant to all Apollo panoramic images
    param_dict['microns'] = 5

    # todo: these values are available in scanned pdfs but not in csv.
    # Hardcoding values from one of the image for now
    param_dict['vel_azm'] = 270
    param_dict['vel_horiz'] = 1.61
    param_dict['vel_radial'] = 0.1

    return param_dict


def check_cub_metadata(image_cube):
    is_metadata_valid = True
    message = ''

    try:
        _ = isis.getkey(image_cube, grpname='Instrument', keyword='InstrumentId') #.stdout.strip()
        _ = isis.getkey(image_cube, grpname='Kernels', keyword='NaifFrameCode')
    except Exception as ex:
        if f'[InstrumentId] does not exist in [Group = Instrument]' in ex.stderr:
            is_metadata_valid = False
            message = f'Metadata error. Metadata for {image_cube} is not complete, "Instrument" is missing'
        elif f'[NaifFrameCode] does not exist in [Group = Kernels]' in ex.stderr:
            is_metadata_valid = False
            message = f'Metadata error. Metadata for {image_cube} is not complete, "Kernels" is missing'
        else:
            raise

    return is_metadata_valid, message


def get_artifacts_prefix(path):
    if path:
        return Path(path).name
    else:
        return ''


def goodness_of_fit_basic_coreg(stats_file):
    """
    Collect statistics for basic co-registration
    """
    shutil.copy(stats_file, stats_file + '.initial.csv')

    df_stats = pd.read_csv(stats_file, skiprows=[1])
    df_stats.to_csv(stats_file + '.final.csv', index=False, na_rep='NA')
    df_stats['PointId,Filename,MeasureType,GoodnessOfFit'.split(',')].to_csv(stats_file, index=False, na_rep='NA')

    gof_mean = df_stats['GoodnessOfFit'].mean(skipna=True)
    ql_of_uncertainty = (
            df_stats.loc[df_stats['GoodnessOfFit'] < QL_THRESHOLD, 'GoodnessOfFit'].count() / df_stats['GoodnessOfFit'].count())
    return gof_mean, ql_of_uncertainty


def goodness_of_fit_adv_coreg(stats_file, interim_pvl_path, scale):
    """
    Collect statistics for advanced co-registration
    """
    df_stats = pd.read_csv(stats_file)
    if 'Filtered' in df_stats.columns:
        df_stats = df_stats[df_stats['Filtered'] != 1]

    gof_mean = df_stats['GoodnessOfFit'].mean(skipna=True)
    ql_of_uncertainty = df_stats[['SampleDifference', 'LineDifference']].std(ddof=0) * scale / 2.

    # cnt_ignored = pvl.count_ignored(interim_pvl_path)
    # cnt_total = df_stats['GoodnessOfFit'].count()
    # ql_of_uncertainty = 1 - cnt_total / (cnt_total + cnt_ignored)
    # ql_of_uncertainty = (
    #         df_stats.loc[df_stats['GoodnessOfFit'] < QL_THRESHOLD_ADV, 'GoodnessOfFit'].count() / df_stats['GoodnessOfFit'].count())
    return (gof_mean, *ql_of_uncertainty)

