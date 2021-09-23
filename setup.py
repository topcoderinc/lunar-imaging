#!/usr/bin/env python3
import click
import os
import time
import subprocess
import validation as v

@click.command()
@click.option('--base_data', is_flag=True, help='If True base data is downloaded')
@click.option('--missions', default=None, required=True, help='Space mission names separated by comma NO WHITE SPACES. For example: lro,apollo15')
def setup(base_data, missions):
    '''This is the entry point to the application'''
    start = time.time()
    print('[INFO] Setup NASA Lunar Co-Registration Tool Started: time {:.2f} secs '.format(time.time() - start))
    try:
        # ISIS env checkup
        print('[INFO] Checking ISIS environment ... time {:.2f} secs '.format(time.time() - start))
        isisroot = os.environ['ISISROOT']
        isisdata = os.environ['ISISDATA']
        isistestdata = os.environ['ISISTESTDATA']
        print('[INFO] $ISISDATA', isisdata)
        print('[INFO] $ISISROOT', isisroot)
        print('[INFO] $ISISTESTDATA', isistestdata)
        
        # checking the isis env
        if v.validate_isis_env(isisroot, isisdata, isistestdata) == -1:
            print('[INFO] The ISIS environment seems not correctly initialized')
            exit()
        
        # checking passed missions
        # data preparation - base data
        if base_data == True:
            print('[INFO] Downloading base data ... time {:.2f} secs '.format(time.time() - start))
            return_code = subprocess.call('rsync -azv --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/base ' + isisdata, shell=True)
            print(return_code)
            if return_code != 0:
                print('[INFO] There was a problem during ISIS base data downloading, please try again.')
                exit()

        # data preparation - missions data
        mission_names = missions.split(',')
        for mission in mission_names:
            return_code = v.validate_mission(mission)
            if return_code != 0:
                print('[INFO] Mission ' + mission + ' skipped because not managed by ISIS ... time {:.2f} secs '.format(time.time() - start))
                continue
            print('[INFO] Downloading ' + mission + ' data ... time {:.2f} secs '.format(time.time() - start))
            return_code = subprocess.call('rsync -azv --exclude="kernels" --delete --partial isisdist.astrogeology.usgs.gov::isisdata/data/' + mission + ' ' + isisdata, shell=True)
            if return_code != 0:
                print('[INFO] There was a problem during ISIS ' + mission + ' data downloading, please try again.')
                exit()
                    
    except Exception as ex:
        print('[ERROR] There was a problem with the tool, please check error trace')
        print('[ERROR] Exception details: ', ex.stderr)
    print('[INFO] Setup NASA Lunar Co-Registration Tool Ended: time {:.2f} secs '.format(time.time() - start))

if __name__ == '__main__':
    setup()
