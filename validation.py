#!/usr/bin/env python3
import os
import helper as h

def validate_isis_env(isisroot, isisdata, isistestdata):
    '''Checking the passed ISIS environemnt variables are initialized'''
    if isisroot is None or isisdata is None or isistestdata is None:
        return -1
    return 0

def validate_apollo(image_folder, apollo_camera):
    '''Validations over the passed Apollo image'''
    # the passed folder must exists
    if os.path.exists(image_folder) == False:
        return -1

    # the passed folder must be not empty
    list_of_images = []
    if apollo_camera == 'metric':
        list_of_images = [f for f in os.listdir(image_folder) if os.path.splitext(f)[1] in h.apollo_metric_file_types]
    elif apollo_camera == 'panoramic':
        list_of_images = [f for f in os.listdir(image_folder) if os.path.splitext(f)[1] in h.apollo_pan_file_types]

    if len(list_of_images) == 0:
        return -2
    return 0

def validate_lro(image_folder):
    '''Validations over the passed LROC image'''
    # the passed image must exists
    if os.path.exists(image_folder) == False:
        return -1

    # the passed folder must be not empty
    list_of_images = [f for f in os.listdir(image_folder) if os.path.splitext(f)[1] in h.lroc_file_types]
    if len(list_of_images) == 0:
        return -2
    return 0

def validate_lo(image_folder):
    '''Validations over the passed Apollo15 image'''
    # the passed folder must exists
    if os.path.exists(image_folder) == False:
        return -1

    # the passed folder must be not empty
    list_of_images = [f for f in os.listdir(image_folder) if os.path.splitext(f)[1] in h.lo_file_types]
    if len(list_of_images) == 0:
        return -2
    return 0

def validate_mission(mission):
    if mission in h.lunar_missions_acronyms:
        return 0
    return -1
    

