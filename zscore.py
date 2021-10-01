from scipy import stats
import numpy as np


def get_boundaries_iqr(df_in, col_name, iqr_coeff=1.5):
    """ Getting a df_in[col_name] 'normal' values range based on the interquartile range.
    Points outside the range might be considered as outliers"""
    q1 = df_in[col_name].quantile(0.25)
    q3 = df_in[col_name].quantile(0.75)
    iqr = q3 - q1  #Interquartile range
    min_ = q1 - iqr_coeff * iqr
    max_ = q3 + iqr_coeff * iqr
    return min_, max_


def mad(x):
    """ Median absolute deviation """
    med = np.median(x, axis=None)
    mad = np.median(np.abs(x - med))
    return mad


def modified_zscore(x):
    """
    Modified z-score calculation.
    Adaptation of regular z-score to the small sample size (number of data points) case.
    Points with with modified_zscore > specific threshold (~3.0-3.5) might be considered as outliers

    Based on:
    "NIST/SEMATECH e-Handbook of Statistical Methods",
    https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
    """
    res = 0.6745 * (x - np.median(x)) / mad(x)
    return res

