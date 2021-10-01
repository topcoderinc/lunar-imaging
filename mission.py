#!/usr/bin/env python3
import os
import pathlib
import shutil
import time
from typing import List, Tuple, Dict, TextIO, Any, Union

import kalasiris as isis
import helper as h
import pvl

def lo_img_preprocess(image, output_folder, coreg_type):
    """ The passed image label is used for image preprocessing before co-registration"""
    # image name without extension
    image_name = h.filename_frompath_noext(image)  # os.path.basename(image)  #
    image_cube = os.path.join(output_folder, image_name + '.cub')
    #image_cube = os.path.join(output_folder, os.path.basename(image) + '.cub')
    
    print('--> [INFO] Importing image: ', image)
    if False:
        pass
    # elif image.endswith('.lbl') or image.endswith('.LBL'):
    #     #image_cube_temp = os.path.join(output_folder, image_name + '.temp.cub')
    #     #isis.pds2isis(from_ = image, to = image_cube_temp)
    #     isis.lo2isis(from_=image, to=image_cube)
    elif image.endswith('.img') or image.endswith('.IMG'):
        isis.lo2isis(from_=image, to=image_cube)
    elif image.endswith('.cub') or image.endswith('.CUB'):
        shutil.copy(image, image_cube)
    elif image.endswith('.jp2') or image.endswith('.JP2'):
        isis.std2isis(from_=image, to=image_cube)
    else:
        print('[INFO] Unsupported Lunar Orbiter image type', image)
        exit()

    # check metadata
    is_valid, description = h.check_cub_metadata(image_cube)
    if not is_valid:
        print('[ERROR] ', description)
        exit()

    print('--> [INFO] Initializing SPICE data')
    isis.spiceinit(web='yes', from_=image_cube, cksmithed=True, spksmithed=True)

    image_cube_heq = image_cube
    ##-- since we usually use "cosmetic" type of LO images it's better to skip these steps
    # print('--> [INFO] Histogram initialization')
    # image_cube_heq = os.path.join(output_folder, image_name + '.heq.cub')
    # isis.histeq(from_=image_cube, to=image_cube_heq)
    # image_cube_heq_rot = os.path.join(output_folder, image_name + '.heq.rot.cub')
    # isis.rotate(from_ = image_cube_heq, to = image_cube_heq_rot, degrees=h.isis_apollo_rotation_angle)
    ##--

    if coreg_type == 'basic':
        print('--> [INFO] Camstat')
        isis.camstats(from_=image_cube_heq, sinc=h.isis_sinc, linc=h.isis_linc, attach=True)
        print('--> [INFO] Footprint')
        isis.footprintinit(from_=image_cube_heq, sinc=h.isis_sinc_foot, linc=h.isis_linc_foot)

    #h.delete_files_with_ckeck([image_cube, image_cube_heq], output_folder)
    
    return image_cube_heq


def apollo_img_preprocess(image, output_folder, coreg_type, mission='apollo15'):
    """ The passed image label is used for image preprocessing before co-registration"""
    # image name without extension
    image_name = h.filename_frompath_noext(image)  # os.path.basename(image)  #
    image_cube = os.path.join(output_folder, image_name + '.cub')
    #image_cube = os.path.join(output_folder, os.path.basename(image) + '.cub')

    print('--> [INFO] Importing image: ', image)
    if image.endswith('.lbl') or image.endswith('.LBL'):
        isis.apollo2isis(from_=image, to=image_cube)
    elif image.endswith('.cub') or image.endswith('.CUB'):
        # image_cube = image
        shutil.copy(image, image_cube)
    elif image.endswith('.jp2') or image.endswith('.JP2'):
        isis.std2isis(from_=image, to=image_cube)
    else:
        print('[INFO] Unsupported APOLLO image type', image)
        exit()

    # check metadata
    is_valid, description = h.check_cub_metadata(image_cube)
    if not is_valid:
        print('[ERROR] ', description)
        exit()

    print('--> [INFO] Initializing SPICE data')
    isis.spiceinit(web='yes', from_=image_cube, cksmithed=True, spksmithed=True)

    print('--> [INFO] Initializing reseau points')
    isis.apollofindrx(from_=image_cube, tolerance=0.01)

    print('--> [INFO] Warping')
    image_cube_warp = os.path.join(output_folder, image_name + '.warped.cub')
    isis.apollowarp(from_=image_cube, to=image_cube_warp)

    image_cube_cal = os.path.join(output_folder, image_name + '.warped.cal.cub')
    if mission == 'apollo15':
        # for Apollo15 specific calibration command is available
        print('--> [INFO] Calibration')
        isis.apollocal(from_=image_cube_warp, to_=image_cube_cal)
    else:
        # do histogram equalization for other missions
        print('--> [INFO] Histogram initialization')
        isis.histeq(from_=image_cube_warp, to=image_cube_cal)

    if coreg_type == 'basic':
        print('--> [INFO] Calculating camstats')
        isis.camstats(from_=image_cube_cal, sinc=h.isis_sinc, linc=h.isis_linc, attach=True)
        print('--> [INFO] Initializing footprints')
        isis.footprintinit(from_=image_cube_cal, sinc=h.isis_sinc_foot, linc=h.isis_linc_foot)

    h.delete_files_with_ckeck([image_cube, image_cube_warp], output_folder)

    return image_cube_cal


def lro_img_preprocess(image, output_folder, coreg_type):
    """ The passed image is used for image preprocessing before co-registration"""
    image_name = h.filename_frompath_noext(image)  # os.path.basename(image)  #
    image_cube = os.path.join(output_folder, image_name + '.cub')
    #image_cube = os.path.join(output_folder, os.path.basename(image) + '.cub')
    
    print('--> [INFO] Importing image: ', image)
    if image.endswith('.img') or image.endswith('.IMG'):
        isis.lronac2isis(from_=image, to=image_cube)
    elif image.endswith('.cub') or image.endswith('.CUB'):
        # image_cube = image
        shutil.copy(image, image_cube)
    elif image.endswith('.jp2') or image.endswith('.JP2'):
        isis.std2isis(from_=image, to=image_cube)
    else:
        print('[INFO] Unsupported LROC image type', image)
        exit()

    # check metadata
    is_valid, description = h.check_cub_metadata(image_cube)
    if not is_valid:
        print('[ERROR] ', description)
        exit()

    print('--> [INFO] Initializing SPICE data')
    isis.spiceinit(web='yes', from_= image_cube)
    
    print('--> [INFO] Performing radiometric correction')
    image_cube_cal = os.path.join(output_folder, image_name + '.cal.cub')
    isis.lronaccal(from_=image_cube, to=image_cube_cal)
    
    print('--> [INFO] Removing echo effects')
    image_cube_cal_echo = os.path.join(output_folder, image_name + '.cal.echo.cub')
    isis.lronacecho(from_=image_cube_cal, to=image_cube_cal_echo)

    if coreg_type == 'basic':
        print('--> [INFO] Calculating camstats')
        isis.camstats(from_=image_cube_cal_echo, sinc=h.isis_sinc, linc=h.isis_linc, attach=True)
        print('--> [INFO] Initializing footprints')
        isis.footprintinit(from_=image_cube_cal_echo, sinc=h.isis_sinc_foot, linc=h.isis_linc_foot)

    h.delete_files_with_ckeck([image_cube, image_cube_cal], output_folder)
    
    return image_cube_cal_echo


def apollo_pan_img_preprocess(image_path, output_folder, coreg_type, mission):
    """ The passed image label is used for image preprocessing before co-registration"""
    image_path = pathlib.Path(image_path)
    image_cube = pathlib.Path(output_folder) / image_path.with_suffix('.cub').name

    # check if it's image or ISIS cube already
    if image_path.suffix == '.cub':
        # cube already
        shutil.copy(image_path, image_cube)
    else:
        print('--> [INFO] Importing image: ', str(image_path))
        isis.std2isis(from_=image_path, to=image_cube)

    print('--> [INFO] Initializing with apollopaninit')
    pan_params = h.get_apollo_pan_params(image_path.stem, mission)
    isis.apollopaninit(from_=image_cube,
                       microns=pan_params['microns'],
                       mission=mission,
                       gmt=pan_params['gmt'],
                       lon_nadir=pan_params['lon_nadir'],
                       lat_nadir=pan_params['lat_nadir'],
                       craft_altitude=pan_params['spacecraft_altitude'],
                       lon_int=pan_params['lon_int'],
                       lat_int=pan_params['lat_int'],
                       vel_azm=pan_params['vel_azm'],
                       vel_horiz=pan_params['vel_horiz'],
                       vel_radial=pan_params['vel_radial'])

    print('--> [INFO] Downscaling cube')
    image_cube_reduced = pathlib.Path(output_folder) / image_cube.with_suffix('.x20' + '.cub').name
    isis.reduce(from_=image_cube, to=image_cube_reduced, sscale=20, lscale=20)
    #image_cube_reduced = image_cube

    print('--> [INFO] Histogram equalization')
    image_cube_cal = image_cube_reduced.with_suffix('.cal.cub')
    isis.histeq(from_=image_cube_reduced, to=image_cube_cal)
    #image_cube = image_cube_to

    if coreg_type == 'basic':
        print('--> [INFO] Initializing footprints')
        isis.camstats(from_=image_cube_cal, sinc=h.isis_sinc, linc=h.isis_linc, attach=True)
        isis.footprintinit(from_=image_cube_cal, sinc=h.isis_linc_foot, linc=h.isis_linc_foot)

    #h.delete_files_with_ckeck([image_cube, image_cube_reduced], output_folder)

    return image_cube_cal.resolve()


def create_file_list(list_of_cubs, file_list_name, output_folder):
    """ Creates a file with the list of cub files to be used for co-registration"""
    
    # compose a file name used to identify resources of the passed list of CUB files
    for cub in list_of_cubs:
        cub_base = os.path.basename(cub)
        cub_base_noext = cub_base.split('.')[0]
        file_list_name = file_list_name + '_' + cub_base_noext
    
    file_list_path = os.path.join(output_folder, file_list_name + '.lis')
    with open(file_list_path, "w") as fhandle:
        for cub in list_of_cubs:
            fhandle.write(os.path.join(output_folder, cub) + '\n')
    return file_list_path


def basic_coregistration(list_of_cubs, output_folder, artifacts_prefix):
    """ Performs basic coregistraion on the passed list of CUB images"""
    
    # create a .lis file containing the list of CUB files
    file_list_name = artifacts_prefix  #'imgs'
    file_list = create_file_list(list_of_cubs, file_list_name, output_folder)
    
    # start co-registration steps
    over_list = file_list + '.ovr'
    errors = os.path.join(output_folder, f'{artifacts_prefix}_err.txt')
    #stats = os.path.join(output_folder, 'stats.txt')
    #log = os.path.join(output_folder, file_list_name + '_cnetref.log')

    isis.findimageoverlaps(fromlist=file_list, overlaplist=over_list, errors=errors)
    file_list_net = os.path.join(output_folder, file_list_name + '.net')
    isis.autoseed(fromlist=file_list, overlaplist=over_list, deffile=h.grid_definition, onet=file_list_net,
                  networkid=file_list_name, pointid="???????", description=file_list_name)
    #isis.overlapstats(fromlist=file_list, overlaplist=over_list, detail='FULL', to=stats, tabletype='TAB')
    file_list_ref_net = os.path.join(output_folder, file_list_name + '.ref.net')
    isis.cnetref(fromlist=file_list, cnet=file_list_net, onet=file_list_ref_net) #, log=log)

    file_list_pointreg = os.path.join(output_folder, file_list_name + '.pointreg.net')
    stats_file = os.path.join(output_folder, h.get_stats_filename(artifacts_prefix))
    isis.pointreg(fromlist=file_list, cnet=file_list_ref_net, deffile=h.pointreg_template,
                  onet=file_list_pointreg, flatfile=stats_file, OUTPUTIGNORED=True, OUTPUTFAILED=True)

    gof_mean, ql_of_uncertainty = h.goodness_of_fit_basic_coreg(stats_file)
    print(f'[INFO] Total level of uncertainty (0..1, lower is better): {ql_of_uncertainty:.3f}')
    print(f'[INFO] Total goodness of co-registration fit (0..1, higher is better): {gof_mean:.3f}')


def advanced_coregistration(old_cubs: List, lroc_cubs: List, output_folder, filter_cn, coreg_config=h.coreg_config, scale=h.scale):
    """ Performs advanced coregistraion on the passed list of CUB images - NOTE: not tested, to be completed"""

    #output_folder = pathlib.Path(output_folder)
    for old_cub in old_cubs:
        for lroc_cub in lroc_cubs:
            adv_coreg_exec(pathlib.Path(old_cub), pathlib.Path(lroc_cub),
                           pathlib.Path(output_folder), filter_cn, pathlib.Path(coreg_config), scale)


def adv_coreg_exec(old_cub: pathlib.Path, lroc_cub: pathlib.Path, output_folder: pathlib.Path,
                   filter_cn: bool, coreg_config: pathlib.Path, scale: int, transform=h.transform):
    #print(f'coreg_config: {coreg_config}  scale: {scale}')

    # match cubes
    print(f'[INFO] Starting co-registration: {old_cub.stem} & {lroc_cub.stem}')
    print(f'--> [INFO] Converting a cube to a different camera geometry')
    matched_cub = output_folder / f'{old_cub.stem}--match--{lroc_cub.stem}.cub'
    isis.cam2cam(from_=old_cub, to_=matched_cub, match=lroc_cub)

    # scale (reduce)
    print(f'--> [INFO] Reducing cubes')
    matched_scaled_cub = output_folder / f'{matched_cub.stem}.x{scale}.cub'
    lroc_scaled_cub = output_folder / f'{lroc_cub.stem}.x{scale}.cub'
    isis.reduce(from_=matched_cub, to_=matched_scaled_cub, sscale=scale, lscale=scale)
    isis.reduce(from_=lroc_cub, to_=lroc_scaled_cub, sscale=scale, lscale=scale)

    # deleting temporary files
    h.delete_files_with_ckeck([matched_cub], output_folder)

    # coreg
    print(f'--> [INFO] Performing co-registration')
    res_name = f'{coreg_config.stem}-{old_cub.stem}-{lroc_cub.stem}.x{scale}'
    interim_cn_path = output_folder / f'{res_name}.interim.net'
    stats_path = output_folder / f'{res_name}.stats.txt'

    try:
        isis.coreg(from_=matched_scaled_cub,
                   match=lroc_scaled_cub,
                   deffile=coreg_config,
                   to_=output_folder / f'{res_name}.{transform}.cub',
                   onet=interim_cn_path,
                   flatfile=stats_path,
                   transform=transform)
    except Exception as ex:
        if f'**USER ERROR** Coreg was unable to register any points' in ex.stderr:
            print('--> [INFO] Advanced co-registration procedure was unable to register any points. Try to use basic co-registration')
            return
        else:
            raise

    # convert interim binary .net to text .pvl
    interim_pvl_path = interim_cn_path.with_suffix('.pvl')
    isis.cnetbin2pvl(from_=interim_cn_path, to_=interim_pvl_path)

    # filtering resulting .pvl
    cnt_filtered = 0
    if filter_cn:
        # print(interim_pvl_path, stats_path)
        flt_pvl_path = interim_pvl_path.with_suffix('').with_suffix('.filtered.pvl')
        cnt_filtered = pvl.filter_coreg_result(interim_pvl_path, stats_path, flt_pvl_path)
        print(f'--> [INFO] Filtered points: {cnt_filtered}')

    if not cnt_filtered:
        flt_pvl_path = interim_pvl_path

    # creating Control Network for source images (converting interim CN to final)
    res_name = f'{coreg_config.stem}-{old_cub.stem}-{lroc_cub.stem}'
    pvl.translate_coreg_res(flt_pvl_path, old_cub, lroc_cub, output_folder, res_name)

    # collecting coreg stats
    gof_mean, uncertainty_samples, uncertainty_lines = h.goodness_of_fit_adv_coreg(stats_path, flt_pvl_path, scale)
    print(f'--> [INFO] Quantified level of uncertainty (Samples, Lines) in LROC pixels: '
          f'({uncertainty_samples:.1f}, {uncertainty_lines:.1f})')
    print(f'--> [INFO] Total goodness of co-registration fit (0..1, higher is better): {gof_mean:.3f}')
