from scipy import stats
import numpy as np


def get_boundaries_iqr(df_in, col_name, iqr_coeff=1.5):
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3 - q1  #Interquartile range
    min_ = q1 - iqr_coeff * iqr
    max_ = q3 + iqr_coeff * iqr
    return min_, max_


def mad(x):
    med = np.median(x, axis=None)
    mad = np.median(np.abs(x - med))
    return mad


def modified_zscore(x):
    res = 0.6745 * (x - np.median(x)) / mad(x)
    return res

