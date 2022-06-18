import pandas as pd
import numpy as np


# POI diversity index
def get_ix(df, r):
    return np.power(df.count(), r)


def get_risk(dff, r):
    dr = dff.groupby('class2', as_index=True).apply(get_ix, r)
    rr = np.power(np.sum(dr), 1 / (1 - r))
    return rr


if __name__ == "__main__":
    df = pd.read_csv('poi.csv')  # read POI data
    jd_df = pd.read_csv('pop.csv')  # read population data

    # test 50 vaules of the exponential factor
    for i in np.arange(0, 1, 0.02):
        jd_hci = df[['jd_id', 'class2']].groupby('jd_id', as_index=True).apply(get_risk, i).rename(
            columns={'class2': 'hci%.1f' % i})['hci%.1f' % i]
        jd_df = pd.merge(jd_df, jd_hci, left_on='jd_id', right_index=True, how='left').fillna(0)
    jd_df.to_csv('HCI.csv')
