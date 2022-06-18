# -*- coding:utf-8 -*-
import datetime as dt
import pandas as pd

import numpy as np
import random
from scipy.stats import binom


def date_range_selection(Case_data, start_date, end_date):
    mask = (Case_data['date'] >= start_date) & (Case_data['date'] <= end_date)
    cd = Case_data.loc[mask]
    return cd


def select_od_data(od):
    df_od = pd.read_csv(od, sep=',', index_col=False)[['year', 'month', 'day', 'hour', 'jd_id_o', 'jd_id_d', 'cnt']]
    df_od['date'] = pd.to_datetime(df_od[['year', 'month', 'day', 'hour']], format="%d/%m/%Y %H")

    return df_od[df_od['jd_id_o'] != df_od['jd_id_d']]


def daily_od_data(od, strr):
    flow = od.groupby(['date', strr], as_index=False).agg({'cnt': np.sum}).rename(columns={strr: 'jd_id'})

    return flow


def CTI_risk(odi_out, odi_in, popi, ipc, start_date, end_date, start_t):
    df_lo = pd.read_csv(popi, index_col=False)
    pop_df = df_lo[['jd_id', 'pop']]

    id_list = df_lo['jd_id'].tolist()

    # initial cases
    case = pd.read_csv(ipc)
    case['date'] = pd.to_datetime(case['date'])
    case = date_range_selection(case, start_date, end_date).groupby(['jd_id'], as_index=False). \
        agg({'cases': np.sum}).rename(columns={'cases': 'New_cases'})

    new_case = pd.DataFrame({'jd_id': id_list, 'New_cases': [0 for i in range(len(set(id_list)))]})
    cumc = pd.merge(case, new_case, on="jd_id", how="right").fillna(0)
    cumc['New_cases'] = cumc.apply(lambda x: x['New_cases_x'] + x['New_cases_y'], axis=1)

    # dataframes for hourly infections and cumulative number of hourly infections
    new_c = new_case.rename(columns={'New_cases': 'New_inf'})
    new_cc = new_case

    # hourly inflow anf outflow
    od_out = select_od_data(odi_out)
    od_in = select_od_data(odi_in)
    dailyod_out = daily_od_data(od_out, 'jd_id_o').rename(columns={'cnt': 'flow_out'})
    dailyod_in = daily_od_data(od_in, 'jd_id_d').rename(columns={'cnt': 'flow_in'})
    flow = pd.merge(dailyod_out, dailyod_in, on=['date', 'jd_id'], how='outer').fillna(0)

    for i in range(48):
        # get population at a given hour
        dfl = flow[flow['date'] == start_t]
        pop_df = pd.merge(pop_df, dfl, on='jd_id', how='left').fillna(0)
        pop_df['pop'] = pop_df['pop'] + pop_df['flow_in'] - pop_df['flow_out']
        index_list = pop_df.loc[(pop_df['pop'] <= 0) | (pop_df['pop'].isnull()), 'pop'].index.tolist()
        pop_df.loc[(pop_df['pop'] <= 0) | (pop_df['pop'].isnull()), 'pop'] = 0.2 * pop_df.loc[index_list, 'pop']

        # get OD flow at a given hour
        f_out = od_out[od_out['date'] == start_t].rename(columns={'jd_id_o': 'jd_id', 'cnt': 'flow_out'})
        f_in = od_in[od_in['date'] == start_t].rename(columns={'jd_id_o': 'jd_id', 'cnt': 'flow_in'})
        m_out = pd.merge(f_out, cumc[['jd_id', 'New_cases']], on='jd_id', how="left").fillna(0)
        m_out = pd.merge(m_out, pop_df[['jd_id', 'pop']], on='jd_id', how="left").fillna(0)

        # compute inter-community movement of cases
        m_out['New_cases_new'] = (m_out['New_cases'] * (m_out['flow_out'] / m_out['pop']))
        new_case_out = m_out[['jd_id', 'New_cases_new']].groupby(['jd_id'], as_index=False).agg(
            {'New_cases_new': np.sum}).rename(columns={'New_cases_new': 'new_cases_out'})

        m_in = pd.merge(f_in, cumc[['jd_id', 'New_cases']], on='jd_id', how="left").fillna(0)
        m_in = pd.merge(m_in, pop_df[['jd_id', 'pop']], on='jd_id', how="left").fillna(0)
        m_in['New_cases_new'] = (m_in['New_cases'] * (m_in['flow_in'] / m_in['pop']))
        new_case_in = m_in[['jd_id_d', 'New_cases_new']].groupby(['jd_id_d'], as_index=False).agg(
            {'New_cases_new': np.sum}).rename(columns={'jd_id_d': 'jd_id', 'New_cases_new': 'new_cases_in'})

        # number of cases at a given hour
        cumc = pd.merge(cumc[['jd_id', 'New_cases']], new_case_in, on="jd_id", how="left").fillna(0)
        cumc = pd.merge(cumc, new_case_out, on="jd_id", how="left").fillna(0)
        cumc['New_cases'] = cumc.apply(lambda x: x['New_cases'] + x['new_cases_in'] - x['new_cases_out'], axis=1)
        cumc = cumc[['jd_id', 'New_cases']]
        pop_df = pop_df[['jd_id', 'pop']]
        cumc.loc[(cumc['New_cases'] < 0) | (cumc['New_cases'].isnull()), 'New_cases'] = 0

        # compute intra-community transmission rate derived from the logged POI-based diversity index
        risk = pd.read_csv('poi.csv')[['jd_id', 'class2']].rename(columns={'class2': 'risk'})
        risk['risk'] = np.log(risk['risk'].astype('float64')) / np.log(np.max(risk['risk'].astype('float64')))

        # compute hourly new infections within a community
        new_case_within = pd.merge(cumc, pop_df, on="jd_id", how="left").fillna(0)
        new_case_within = pd.merge(new_case_within, risk, on="jd_id", how="left").fillna(0)
        new_case_within['namda'] = new_case_within['New_cases'] * new_case_within['risk'] / new_case_within[
            'pop']  # infection rate
        new_case_within['p_stay'] = new_case_within['pop'] - new_case_within['New_cases']

        index_list = new_case_within.loc[new_case_within['p_stay'] <= 0, 'p_stay'].index.tolist()
        new_case_within.loc[new_case_within['p_stay'] <= 0, 'p_stay'] = 0.2 * new_case_within.loc[index_list, 'pop']
        new_case_within.loc[new_case_within['namda'] >= 0.8, 'namda'] = 0.8

        new_case_within['New_cases_stay'] = new_case_within.apply(
            lambda x: np.mean(binom.rvs(int(x['p_stay']), x['namda'], 100)), axis=1)  # new infections at a given hour

        new_c = pd.merge(new_c, new_case_within[['jd_id', 'New_cases_stay']], on="jd_id", how="left").fillna(0)
        new_c['New_inf'] = new_c['New_inf'] + new_c['New_cases_stay']

        new_c['New_inf%d' % i] = new_c['New_cases_stay']

        # number of hourly infections
        new_cc = pd.merge(new_cc, new_c[['jd_id', 'New_inf%d' % i]], on="jd_id", how="left").fillna(0)

        new_c = new_c[['jd_id', 'New_inf']]

        start_t = start_t + dt.timedelta(hours=1)

    return new_cc


if __name__ == "__main__":
    ipc = 'newcases.csv'
    odi_out = 'jd_outOD.csv'
    odi_in = 'jd_inOD.csv'
    popi = 'pop.csv'
    start_t = dt.datetime(2020, 6, 11, 0)
    start_date = dt.datetime(2020, 6, 13)
    end_date = dt.datetime(2020, 6, 15)

    df_lo = pd.read_csv(popi, index_col=False)
    id_list = df_lo['jd_id'].tolist()  # ID of all communities
    new_case = pd.DataFrame({'jd_id': id_list})
    col_names = ['jd_id']

    # cumulative number of hourly infections
    for t in range(48):
        new_case['New_cases%d' % t] = [0 for i in range(len(set(id_list)))]
        col_names.append('New_cases%d' % t)

    df = CTI_risk(odi_out, odi_in, popi, ipc, start_date, end_date, start_t)
    new_case = pd.merge(new_case, df, on='jd_id', how='left').fillna(0)
    for ii in range(48):
        new_case['New_cases%d' % ii] = new_case['New_cases%d' % ii] + new_case['New_inf%d' % ii]
    new_case = new_case[col_names]

    new_case.to_csv('bj_CTI_hour.csv', index=False, encoding='gbk')
