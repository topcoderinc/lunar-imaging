#from skimage.io import imread, imsave

from pathlib import Path
#import kalasiris as isis
import pandas as pd

#from PIL import Image
#Image.MAX_IMAGE_PIXELS = None

BASE_PATH = Path('/media/dmitry/SSD/DV/NASA/test/')
image_name = 'AS15-M-1828.jp2'
out_name = 'AS15-M-1828_jp2.tif'
image_cube = '/media/dmitry/SSD/DV/NASA/2021_Topcoder_NASA_FinalRefinement/data/apollo16/output/AS16-M-2909.cub'
QL_THRESHOLD = 0.5

def jpg_to_tiff(image_name, out_name):
    arr = Image.open(BASE_PATH / image_name)
    arr.save(BASE_PATH / out_name, 'TIFF')

def check_cub_metadata(image_cube):
    is_metadata_valid = True
    description = ''

    try:
        _ = isis.getkey(image_cube, grpname='Instrument', keyword='InstrumentId') #.stdout.strip()
        _ = isis.getkey(image_cube, grpname='Kernels', keyword='NaifFrameCode')
    except Exception as ex:
        if f'[InstrumentId] does not exist in [Group = Instrument]' in ex.stderr:
            is_metadata_valid = False
            description = f'Metadata error. Metadata for {image_cube} is not complete, "Instrument" is missing'
        elif f'[NaifFrameCode] does not exist in [Group = Kernels]' in ex.stderr:
            is_metadata_valid = False
            description = f'Metadata error. Metadata for {image_cube} is not complete, "Kernels" is missing'
        else:
            raise

    return is_metadata_valid, description

def catlab(image_cube):
    print(isis.catlab(from_=image_cube).stderr.strip())
    print(isis.catlab(from_=image_cube).stdout.strip())

def goodness_of_fit(stats_file):
    df_stats = pd.read_csv(stats_file, skiprows=[1])
    df_stats['PointId,Filename,MeasureType,Ignore,Registered,GoodnessOfFit'.split(',')].to_csv(stats_file + '.final.csv', index=False, na_rep='NA')

    gof_mean = df_stats['GoodnessOfFit'].mean(skipna=True)
    ql_of_uncertainty = df_stats.loc[df_stats['GoodnessOfFit'] >= QL_THRESHOLD, 'GoodnessOfFit'].count() / df_stats['GoodnessOfFit'].count()
    print(df_stats.loc[df_stats['GoodnessOfFit'] >= QL_THRESHOLD, 'GoodnessOfFit'].count(), df_stats['GoodnessOfFit'].count())
    return gof_mean, ql_of_uncertainty

#def key_test():
#    isis.cube.get_table

if __name__ == '__main__':
    #catlab(image_cube)
    #check_cub_metadata(image_cube)
    stats_file = '/media/dmitry/SSD/DV/NASA/2021_Topcoder_NASA_FinalRefinement/data_flask/output/m_v/pointreg_00.stats.csv'
    gof_mean, ql_of_uncertainty = goodness_of_fit(stats_file)
    print(gof_mean, ql_of_uncertainty)


