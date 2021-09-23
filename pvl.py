import pathlib
from typing import List, Tuple, Dict, TextIO, Any, Union
import shutil
import math
import pandas as pd

import parse
import kalasiris as isis
import helper as h
import zscore


def all_substrings_in(substr_lst: List[str], line: str) -> bool:
    """
    Check if all substrings are in the line.

    """
    ret = True
    for match_str in substr_lst:
        if match_str not in line:
            ret = False
            break

    return ret


def read_till(match_str_lst: List[str], f: TextIO) -> Tuple[List[str], str]:
    head = []
    found_line = ''
    pred_line = ''

    for line in f:
        # some lines in pvl might be split by '-\n' sequence. Join them into one line to process
        if '-\n' in line:
            pred_line = pred_line + line[:-2]
            continue

        if pred_line:
            line = pred_line + line.strip(' ')
            pred_line = ''

        # save the line
        head.append(line)

        # check if all match substrings are in the line. if so - stop reading from the file and return results
        if match_str_lst and all_substrings_in(match_str_lst, line):
            found_line = line
            break

    return head, found_line


def pvlgroup_to_dict(grp: List[str]) -> Dict[str, str]:
    """
    Parse pvl group formatted as list of 'key = value' strings into dictionary

    """
    grp_dict = {}

    for line in grp:
        res = parse.parse('{}={}', line)
        if res:
            k = res.fixed[0].strip()
            v = res.fixed[1].strip()
            grp_dict.update({k: v})

    return grp_dict


def clean_pvldict(pvl_dict: Dict[str, str]) -> Dict[str, Any]:
    cleaned_dict = pvl_dict.copy()

    def update_dict(key, type_):
        val = cleaned_dict.get(key, None)
        if val is not None:
            # in case these are some measurement units in a string
            val = val.split(' ')[0]
            cleaned_dict[key] = type_(val)

    for key in ['Sample', 'Line', 'SampleResidual', 'LineResidual']:
        update_dict(key, float)

    update_dict('Reference', bool)
    return cleaned_dict


def update_pvlgroup(source_pvl: List[str], keys: List[str], pvl_dict: Dict[str, Any]) -> Dict[str, Any]:
    res_pvl = source_pvl.copy()

    for i, line in enumerate(res_pvl):
        for key in keys:
            if all_substrings_in([f' {key} ', ' = '], line):
                res_pvl[i] = f'{key} = {pvl_dict[key]}\n'
    return res_pvl


def write_final_cn(cn: str, output_folder: pathlib.Path, output_cn_name: str):
    temp_pvl_path = output_folder / 'camtp.pvl'

    with open(temp_pvl_path, 'wt') as f:
        f.write(cn)

    # easiest way to format final pvl is converting it back and forth
    output_net_path = output_folder / f'{output_cn_name}.net'
    output_pvl_path = output_folder / f'{output_cn_name}.pvl'
    isis.cnetpvl2bin(from_=temp_pvl_path, to_=output_net_path)
    isis.cnetbin2pvl(from_=output_net_path, to_=output_pvl_path)

    if temp_pvl_path.exists():
        temp_pvl_path.unlink()


def translate_coreg_res(input_pvl_path: pathlib.Path,
                        old_cube_path: pathlib.Path,
                        lroc_cube_path: pathlib.Path,
                        output_folder: pathlib.Path,
                        output_cn_name: str):
    temp_pvl_path = output_folder / 'camtp.pvl'

    with open(input_pvl_path, 'rt') as f:
        line = ' '
        control_network = []

        while line:
            head, line = read_till(['Group', '=', 'ControlMeasure'], f)
            control_network.extend(head)

            pvl_group, line = read_till(['End_Group'], f)
            pvl_dict = clean_pvldict(pvlgroup_to_dict(pvl_group[:-1]))

            # if matched (moved) point
            if 'SerialNumber' in pvl_dict.keys():
                #try:
                # for transformed image. get lat & lon of control point
                isis.campt(from_=output_folder / pvl_dict['SerialNumber'], to_=temp_pvl_path,
                           append=False, sample=pvl_dict['Sample'], line=pvl_dict['Line'])
                lat = isis.getkey_k(temp_pvl_path, group='GroundPoint', key='PlanetocentricLatitude')
                lon = isis.getkey_k(temp_pvl_path, group='GroundPoint', key='PositiveEast360Longitude')

                ## for source image. get sample & line of control point corresponding to found lat & lon
                if pvl_dict.get('Reference'):
                    src_image = lroc_cube_path
                else:
                    src_image = old_cube_path

                isis.campt(from_=src_image, to_=temp_pvl_path, type='ground', append=False,
                           latitude=lat, longitude=lon)
                sample = isis.getkey_k(temp_pvl_path, group='GroundPoint', key='Sample')
                line = isis.getkey_k(temp_pvl_path, group='GroundPoint', key='Line')
                sn = isis.getsn(from_=src_image, format_='flat').stdout.strip()

                pvl_dict['Sample'] = sample
                pvl_dict['Line'] = line
                pvl_dict['SerialNumber'] = sn  # src_image.name  #
                pvl_group = update_pvlgroup(pvl_group, ['Sample', 'Line', 'SerialNumber'], pvl_dict)
                control_network.extend(pvl_group)
                #except Exception as ex:
                #    print(ex.stderr)
            else:
                control_network.extend(pvl_group)

    write_final_cn(''.join(control_network), output_folder, output_cn_name)

    if temp_pvl_path.exists():
        temp_pvl_path.unlink()


def count_ignored(input_pvl_path: pathlib.Path) -> int:
    cnt = 0
    with open(input_pvl_path, 'rt') as f:
        line = ' '
        while line:
            _, line = read_till(['Ignore', '=', 'True'], f)
            if line:
                cnt += 1

    return cnt


def filter_points(stats_path):
    df_stats = pd.read_csv(stats_path)
    df_stats['Filtered'] = 0
    df_stats.to_csv(stats_path, index=False)

    res = []

    # if more than 2 rows - try to filter
    if df_stats.shape[0] > 2:
        df_stats['sample_mod_zscore'] = zscore.modified_zscore(df_stats['SampleDifference'])
        df_stats['line_mod_zscore'] = zscore.modified_zscore(df_stats['LineDifference'])

        df_stats.loc[df_stats['sample_mod_zscore'] >= h.MODIFIED_ZSCORE_THRESH, 'Filtered'] = 1
        df_stats.loc[df_stats['line_mod_zscore'] >= h.MODIFIED_ZSCORE_THRESH, 'Filtered'] = 1

        # if some rows were filtered
        if df_stats['Filtered'].sum() > 0:
            #shutil.copy(stats_path, stats_path.with_suffix('.init.txt'))
            (df_stats.drop(['sample_mod_zscore', 'line_mod_zscore'], axis='columns')
             .to_csv(stats_path, index=False))

        res = list(df_stats.loc[df_stats['Filtered'] == 1].itertuples(index=False))

    return res


def point_in_measures(point_tuples_lst, pvl_dict_measures, abs_tol=0.01):
    res = False

    for point in point_tuples_lst:
        is_the_same_point = (
                (math.isclose(point.Sample, pvl_dict_measures.get('Sample', -1), abs_tol=abs_tol) and
                 math.isclose(point.Line, pvl_dict_measures.get('Line', -1), abs_tol=abs_tol))
                or
                (math.isclose(point.TranslatedSample, pvl_dict_measures.get('Sample', -1), abs_tol=abs_tol) and
                 math.isclose(point.TranslatedLine, pvl_dict_measures.get('Line', -1), abs_tol=abs_tol))
        )

        is_the_same_residual = (
                math.isclose(point.SampleDifference,
                             pvl_dict_measures.get('SampleResidual', -1), abs_tol=abs_tol) and
                math.isclose(point.LineDifference,
                             pvl_dict_measures.get('LineResidual', -1), abs_tol=abs_tol)
        )

        res = is_the_same_point and is_the_same_residual

        if res:
            break

    return res


def filter_coreg_result(input_pvl_path, stats_path, output_pvl_path):
    filtered_points = filter_points(stats_path)
    #print(filtered_points)

    if not filtered_points:
        return 0

    with open(input_pvl_path, 'rt') as f:
        line = ' '
        control_network = []

        while line:
            head, line = read_till(['Object', '=', 'ControlPoint'], f)
            control_network.extend(head)
            # print(f'head:\n {head}\nline:\n{line}\n')

            pvl_group_point, line = read_till(['Group', '=', 'ControlMeasure'], f)
            pvl_dict_point = clean_pvldict(pvlgroup_to_dict(pvl_group_point[:-1]))
            # print(f'pvl_group_point:\n {pvl_group_point}\nline:\n{line}\n')

            # if not ignored point
            if ('PointId' in pvl_dict_point.keys()
                    and 'Ignore' not in pvl_dict_point.keys()):

                pvl_group_measures, line = read_till(['End_Object'], f)
                pvl_dict_measures = clean_pvldict(pvlgroup_to_dict(pvl_group_measures[:-1]))
                # print(f'pvl_group_measures:\n {pvl_group_measures}\nline:{line}\n')
                # print(f'pvl_dict_measures:\n {pvl_dict_measures}\n')

                # if it's filtered point - and "Ignore = True" in pvl for this point
                if point_in_measures(filtered_points, pvl_dict_measures):
                    #print('----!!! Filtered ----')
                    pvl_group_point.insert(0, ' Ignore = True\n')

                    #print(f'pvl_dict_point after:\n {pvl_dict_point}\n')
                    #print(f'pvl_group_point after:\n {pvl_group_point}\n')

                control_network.extend(pvl_group_point)
                control_network.extend(pvl_group_measures)
            else:
                control_network.extend(pvl_group_point)

            # print('====================\n')

    # save Control Network in a binary and text formats
    write_final_cn(''.join(control_network), output_pvl_path.parent, output_pvl_path.stem)

    return len(filtered_points)

