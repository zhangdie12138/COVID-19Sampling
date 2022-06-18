# -*- coding:utf-8 -*-
import datetime as dt
import pandas as pd
import numpy as np


# get cases during a period
def date_range_selection(Case_data, start_date, end_date):
    mask = (Case_data['date'] >= start_date) & (Case_data['date'] <= end_date)
    cd = Case_data.loc[mask]
    return cd


# get OD flow
def select_od_data(od):
    df_od = pd.read_csv(od, sep=',', index_col=False)[['year', 'month', 'day', 'hour', 'jd_id_o', 'jd_id_d', 'cnt']]
    df_od['date'] = pd.to_datetime(df_od[['year', 'month', 'day', 'hour']], format="%d/%m/%Y %H")
    return df_od[df_od['jd_id_o'] != df_od['jd_id_d']]


# get counts of population flows
def daily_od_data(od, strr):
    flow = od.groupby(['date', strr], as_index=False).agg({'cnt': np.sum}).rename(columns={strr: 'jd_id'})
    return flow


def CFI_risk(odi_out, odi_in, popi, ipc, start_date, end_date, start_t):
    df_lo = pd.read_csv(popi, index_col=False)
    pop_df = df_lo[['jd_id', 'pop']]  # population

    id_list = df_lo['jd_id'].tolist()  # ID of all communities

    # initial cases
    new_case = pd.DataFrame({'jd_id': id_list, 'New_cases': [0 for i in range(len(set(id_list)))]})

    case = pd.read_csv(ipc)
    case['date'] = pd.to_datetime(case['date'])
    case = date_range_selection(case, start_date, end_date).groupby(['jd_id'], as_index=False). \
        agg({'cases': np.sum}).rename(columns={'cases': 'New_cases'})

    cumc = pd.merge(case, new_case, on="jd_id", how="right").fillna(0)
    cumc['New_cases'] = cumc.apply(lambda x: x['New_cases_x'] + x['New_cases_y'], axis=1)

    # dataframes for hourly cases and cumulative number of houly cases
    new_c = cumc.rename(columns={'New_cases': 'New_inf'})
    new_cc = cumc.rename(columns={'New_cases': 'New_inf'})

    # OD flows
    od_out = select_od_data(odi_out)
    od_in = select_od_data(odi_in)

    # hourly inflow and outflow
    dailyod_out = daily_od_data(od_out, 'jd_id_o').rename(columns={'cnt': 'flow_out'})
    dailyod_in = daily_od_data(od_in, 'jd_id_d').rename(columns={'cnt': 'flow_in'})
    flow = pd.merge(dailyod_out, dailyod_in, on=['date', 'jd_id'], how='outer').fillna(0)

    # hourly CFI under 48 hours
    for i in range(48):
        # get population at a given hour
        dfl = flow[flow['date'] == start_t]
        pop_df = pd.merge(pop_df, dfl, on='jd_id', how='left').fillna(0)
        pop_df['pop'] = pop_df['pop'] + pop_df['flow_in'] - pop_df['flow_out']

        # get OD flow at a given hour
        f_out = od_out[od_out['date'] == start_t].rename(columns={'jd_id_o': 'jd_id', 'cnt': 'flow_out'})
        f_in = od_in[od_in['date'] == start_t].rename(columns={'jd_id_o': 'jd_id', 'cnt': 'flow_in'})

        # get cases at a given hour
        m_out = pd.merge(f_out, cumc[['jd_id', 'New_cases']], on='jd_id', how="left").fillna(0)
        m_out = pd.merge(m_out, pop_df[['jd_id', 'pop']], on='jd_id', how="left").fillna(0)

        # compute inter-community movement of cases
        # count of case outflow
        m_out['New_cases_new'] = (m_out['New_cases'] * (m_out['flow_out'] / m_out['pop']))
        new_case_out = m_out[['jd_id', 'New_cases_new']].groupby(['jd_id'], as_index=False).agg(
            {'New_cases_new': np.sum}).rename(columns={'New_cases_new': 'new_cases_out'})

        # count of case inflow
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

        # handle negative values
        cumc.loc[(cumc['New_cases'] < 0) | (cumc['New_cases'].isnull()), 'New_cases'] = 0
        pop_df.loc[(pop_df['pop'] < 0) | (pop_df['pop'].isnull()), 'pop'] = 0

        # cumulative number of hourly cases
        new_c = pd.merge(new_c, cumc, on="jd_id", how="left").fillna(0)
        new_c['New_inf'] = new_c['New_inf'] + new_c['New_cases']
        new_c['New_inf%d' % i] = new_c['New_cases']
        new_cc = pd.merge(new_cc, new_c[['jd_id', 'New_inf%d' % i]], on="jd_id", how="left").fillna(0)
        new_c = new_c[['jd_id', 'New_inf']]

        start_t = start_t + dt.timedelta(hours=1)

    return new_cc


if __name__ == "__main__":
    # prepare data
    ipc = 'newcases.csv'  # initial cases
    odi_out = 'jd_outOD.csv'  # outlow
    odi_in = 'jd_inOD.csv'  # inflow
    popi = 'pop.csv'  # population data

    start_t = dt.datetime(2020, 6, 11, 0)  # start hour for population flow data

    # period of cases selected
    start_date = dt.datetime(2020, 6, 13)
    end_date = dt.datetime(2020, 6, 15)

    # run cfi
    df = CFI_risk(odi_out, odi_in, popi, ipc, start_date, end_date, start_t)

    # save hourly results
    df.to_csv('CFI_hourly.csv', index=False, encoding='gbk')
