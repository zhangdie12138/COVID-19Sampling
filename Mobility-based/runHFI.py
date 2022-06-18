# -*- coding:utf-8 -*-
import pandas as pd
import numpy as np


def HFI_risk(odi_out, odi_in):
    df_out = pd.read_csv(odi_out, sep=',', index_col=False)
    df_in = pd.read_csv(odi_in, sep=',', index_col=False)
    # group by origin community
    flow_out = df_out.groupby(['jd_id_o', 'day', 'hour'], as_index=False).agg({'cnt': np.sum}).rename(
        columns={'jd_id_o': 'jd_id', 'cnt': 'flow_out'})
    # group by destination community
    flow_in = df_in.groupby(['jd_id_d', 'day', 'hour'], as_index=False).agg({'cnt': np.sum}).rename(
        columns={'jd_id_d': 'jd_id', 'cnt': 'flow_in'})

    flow = pd.merge(flow_in, flow_out, on=['jd_id', 'day', 'hour'], how='outer').fillna(0)
    flow['flow'] = (flow['flow_in'] + flow['flow_out']) / 10000
    flow[['jd_id', 'day', 'hour', 'flow']].to_csv('HFI_hours.csv', index=False)


if __name__ == "__main__":
    odi_out = 'jd_outOD.csv'  # population outflow data
    odi_in = 'jd_inOD.csv'  # population inflow data
    HFI_risk(odi_out, odi_in)
