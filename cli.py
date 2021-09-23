#!/usr/bin/env python3
import click
import time
import os
from multiprocessing import Pool
from functools import partial
#import pprint

import validation as v
import helper as h
import mission
import pvl

@click.command()
@click.option('--apollo', default=None, required=False, help='Path to the folder containing LBL files associated to Apollo images')
@click.option('--apollo_mission', type=click.Choice(['apollo15', 'apollo16', 'apollo17'], case_sensitive=False),
                default='apollo15', required=False, help='Apollo mission name')
@click.option('--metric', 'apollo_camera', flag_value='metric', default=True)
@click.option('--panoramic', 'apollo_camera', flag_value='panoramic')
@click.option('--lo', default=None, required=False, help='Path to the folder containing LO image files')
@click.option('--lro', default=None, required=False, help='Path to the folder containing LROC image files')
@click.option('--output_folder', default='./output', required=False, help='Folder used to save co-registration resources')
@click.option('--num_proc', type=int, default=1, help='Number of processes for parallel image preprocessing')
@click.option('--basic', 'coreg_type', flag_value='basic')
@click.option('--advanced', 'coreg_type', flag_value='advanced', default=True)
@click.option('--coreg_config', default=h.coreg_config, required=False, help='Path to the co-registration config file (.def)')
@click.option('--scale', type=int, default=h.scale, required=False,
              help='Scale during advanced co-registration (have to match corresponding coreg_config)')
@click.option('--filter_cn', type=int, default=1,
              help='Apply additional filtering of coreg resulting Control Network. Presumably improve coreg quality)')
def cli(apollo, apollo_mission, apollo_camera, lo, lro, output_folder, num_proc, coreg_type, coreg_config, scale, filter_cn):
    '''This is the entry point to the application'''
    args = locals()
    start = time.time()
    print('[INFO] NASA Lunar Co-Registration Tool Started: time {:.2f} secs '.format(time.time() - start))
    #print(f'h.coreg_config: {coreg_config}, h.scale: {scale}')

    try:
        count_missions = 0
        if apollo:
            count_missions += 1
        if lro:
            count_missions += 1
        if lo:
            count_missions += 1

        # two missions must be chosen
        if count_missions <= 1 or count_missions > 2:
            print('[INFO] Two missions must be specified between APOLLO15, LRO, LO')
            exit()

        # validate input parameters
        if apollo:
            validation_code = v.validate_apollo(apollo, apollo_camera)
            if validation_code == -1:
                print('[INFO] The passed Apollo image folder does not exists')
                exit()
            elif validation_code == -2:
                print('[INFO] The passed Apollo image folder does not contain any valid image label')
                exit()
        if lro:
            validation_code = v.validate_lro(lro)
            if validation_code == -1:
                print('[INFO] The passed LROC image folder does not exists')
                exit()
            elif validation_code == -2:
                print('[INFO] The passed LROC image folder does not contain any valid image')
                exit()
        if lo:
            validation_code = v.validate_lo(lo)
            if validation_code == -1:
                print('[INFO] The passed LO image folder does not exists')
                exit()
            elif validation_code == -2:
                print('[INFO] The passed LO image folder does not contain any valid image')
                exit()

        # create the output folder if it does not exists yet
        if not os.path.exists(output_folder):
            h.make_empty_folder(output_folder)
        
        # preprocessed cub files
        #preprocessed_cubs = []
        old_cubs = []
        lroc_cubs = []

        # preprocess apollo
        if apollo:
            print('[INFO] Apollo image preprocessing')  #: time {:.2f} secs '.format(time.time() - start))

            if apollo_camera == 'metric':
                apollo_images = [os.path.join(apollo, f)
                                 for f in os.listdir(apollo)
                                 if os.path.splitext(f)[1] in h.apollo_metric_file_types]

                with Pool(num_proc) as p:
                    f = partial(mission.apollo_img_preprocess,
                                output_folder=output_folder, coreg_type=coreg_type, mission=apollo_mission)
                    res = list(p.imap_unordered(f, apollo_images))
                old_cubs.extend(res)

            elif apollo_camera == 'panoramic':
                apollo_pan_images = [os.path.join(apollo, f)
                                     for f in os.listdir(apollo)
                                     if os.path.splitext(f)[1] in h.apollo_pan_file_types]
                for apollo_image in apollo_pan_images:
                    old_cubs.append(
                        mission.apollo_pan_img_preprocess(os.path.join(apollo, apollo_image), output_folder,
                                                          coreg_type=coreg_type, mission=apollo_mission))

        # preprocess lo images
        if lo:
            print('[INFO] LO image preprocessing')  #: time {:.2f} secs '.format(time.time() - start))
            lo_images = [os.path.join(lo, f) for f in os.listdir(lo) if os.path.splitext(f)[1] in h.lo_file_types]

            with Pool(num_proc) as p:
                f = partial(mission.lo_img_preprocess, output_folder=output_folder, coreg_type=coreg_type)
                res = list(p.imap_unordered(f, lo_images))
            old_cubs.extend(res)

            #for lo_image in lo_images:
            #    preprocessed_cubs.append(
            #       mission.lo_img_preprocess(os.path.join(lo, lo_image), output_folder, coreg_type))

        # preprocess lroc images
        if lro:
            print('[INFO] LROC image preprocessing: time {:.2f} secs '.format(time.time() - start))
            lroc_images = [os.path.join(lro, f) for f in os.listdir(lro) if os.path.splitext(f)[1] in h.lroc_file_types]

            with Pool(num_proc) as p:
                f = partial(mission.lro_img_preprocess, output_folder=output_folder, coreg_type=coreg_type)
                res = list(p.imap_unordered(f, lroc_images))
            lroc_cubs.extend(res)

            #for lro_image in lroc_images:
            #    preprocessed_cubs.append(
            #       mission.lro_img_preprocess(os.path.join(lro, lro_image), output_folder, coreg_type))

        # co-registration
        print('[INFO] Images co-registration: time {:.2f} secs '.format(time.time() - start))

        if coreg_type == 'basic':
            mission_dir = apollo if apollo else lo
            mission.basic_coregistration(old_cubs + lroc_cubs, output_folder, h.get_artifacts_prefix(mission_dir))
        elif coreg_type == 'advanced':
            mission.advanced_coregistration(old_cubs, lroc_cubs, output_folder, filter_cn, coreg_config, scale)

    except Exception as ex:
        print('[ERROR] There was a problem with the tool, please check error trace')
        print('[ERROR] Exception details: ', ex.stderr)
        exit(1)
    finally:
        pass


    print('[INFO] NASA Lunar Co-Registration Tool Ended: time {:.2f} secs '.format(time.time() - start))

if __name__ == '__main__':
    cli()
