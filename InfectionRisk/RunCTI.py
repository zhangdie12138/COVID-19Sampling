# -*- coding:utf-8 -*-

import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform
import gc
import time
from scipy.stats import binom
import random
import math


def get_hourStay(day, t):
    df_stay = pd.read_csv('Flow/day%d/personStay.csv' % day)
    df_stay_t = df_stay[df_stay['hour'] == t]
    return df_stay_t


def get_hourFlow(day, t):
    df_flow = pd.read_csv('Flow/day%d/personFlow.csv' % day)
    df_flow_t = df_flow[df_flow['hour'] == t]
    return df_flow_t


def get_enta(d):
    w1 = 0.4 * np.exp(-0.25 * np.power((d / 6), 2))  # walk 0.3
    enta = (w1 * 0.2 + (0.16 * 0.3 + 0.2 * 0.5 + 0.12 * 0.4 + 0.12 * 0.6) * (1 - w1))
    return enta


def get_risk_s3(tt, df_t_1):
    if tt > 23:
        t = tt - 24
        day = 12
    else:
        t = tt
        day = 11
    cases_t_1 = {}  # 病例字典
    cases_id = df_t_1['grid'].tolist()
    for m in range(len(df_t_1)):
        grid_name = df_t_1.loc[m, 'grid']
        cases_t_1[grid_name] = df_t_1.loc[m, 'cases']

    all_grids = {}  # 所有网格病例字典
    df_grids = pd.read_excel('grid_id.xlsx')
    for gid in df_grids['grid'].tolist():
        if gid in cases_id:
            all_grids[gid] = cases_t_1[gid]
        else:
            all_grids[gid] = 0

    # t时刻有流入的网格n*n
    df_in = pd.read_csv('OD/202006%d%02d-inODMatrix.csv' % (day, t), sep='\t', index_col=False)
    grids_in = df_in['Unnamed: 0'].tolist()

    # 有病例流入的网格m
    common_id = list(set(cases_id).intersection(set(grids_in)))  # 有病例流入的网格
    df_cases = df_t_1[df_t_1['grid'].isin(common_id)]  # 取行m

    # 计算enta
    df_in_location = pd.merge(df_in, df_grids, left_on='Unnamed: 0', right_on='grid', how='left')[['xx', 'yy']]
    df_dist = squareform(pdist(df_in_location, 'euclidean')) / 1000  # 米转KM
    entaji = pd.DataFrame(get_enta(df_dist), columns=grids_in)  # enta矩阵n*n

    del df_in_location, df_dist
    gc.collect()

    flow_t_1 = get_hourFlow(day, t - 1)
    df1 = pd.merge(df_cases, flow_t_1, on='grid', how='left')  # 有病例的网格的流动人口 m个网格的属性
    I_enta = entaji[common_id] * list(df1['cases'] / df1['pop_flow'])  # n*m*m*1
    Iji = df_in[common_id] * list(df1['cases'] / df1['pop_flow'])  # Iji n*m
    PIji = df_in[common_id] * list((1 - df1['cases'] / df1['pop_flow']))
    Iji = Iji.fillna(0)
    PIji = PIji.fillna(0)
    PIji = PIji.applymap(lambda x: math.ceil(x))  # n*m

    # print(PIji.shape)

    del df_in, entaji
    gc.collect()

    # 流入的病例数
    sum_Iji = Iji.apply(lambda x: x.sum(), axis=1)  # 行和 m个相加, n*1
    # print(sum_Iji.shape)

    rand = random.random()
    BP = binom.pmf(1, PIji, I_enta)  # n*m
    # print(BP.shape)
    BP[np.isnan(BP)] = 0
    BPP = (BP > rand) + 0
    betaIji = np.sum(BPP, axis=1)  # 流动中感染的人数 n*1
    # print(betaIji.shape)

    betaIjiDict = {}
    # 流动中增加的感染人数
    for name_inx, name in enumerate(grids_in):
        betaIjiDict[name] = betaIji[name_inx]

    I_in = {}  # 流入的病例数
    for inx, idd in enumerate(grids_in):
        I_in[idd] = sum_Iji.iloc[inx]

    # t时刻有病例流出的格网
    df_out = pd.read_csv('OD/202006%d%02d-outODMatrix.csv' % (day, t), sep='\t', index_col=False)  # 流出矩阵 p*p
    grids_out = df_out['Unnamed: 0'].tolist()  # 有流出的格网ID
    common_id_out = list(set(cases_id).intersection(set(grids_out)))  # 有流出&有病例的网格ID q个
    cases_out = df_t_1[df_t_1['grid'].isin(common_id_out)]  # 有流出&有病例的网格的病例数 （取行） q个的病例数

    # 流出的病例数
    df2 = pd.merge(cases_out, flow_t_1, on='grid', how='left')  # 有流出&有病例的网格的病例数&人数 q
    df_out_cases = df_out[df_out['Unnamed: 0'].isin(common_id_out)].iloc[:, 1:].apply(lambda x: x.sum(),
                                                                                      axis=1)  # 有病例网格的流出 q*p, q*1
    Iikout = list(df_out_cases * list(df2['cases'] / df2['pop_flow']))  # 流出的人口Pik * 病例数Ii / 人口 Pk q*1 q*1 q*1
    I_out_names = df_out[df_out['Unnamed: 0'].isin(common_id_out)]['Unnamed: 0'].tolist()  # 有流出&有病例的网格ID， 按流出矩阵顺序 q个元素

    del df_out, flow_t_1, df2, df_out_cases
    gc.collect()

    I_out = {}  # 流出的病例数
    for ii, idd in enumerate(I_out_names):
        I_out[idd] = Iikout[ii]

    # 所有格网T时刻的确诊病例数
    for gd in all_grids:
        if gd in I_in and gd in I_out:
            all_grids[gd] = all_grids[gd] + I_in[gd] - I_out[gd]
        elif gd in I_in and gd not in I_out:
            all_grids[gd] = all_grids[gd] + I_in[gd]
        elif gd not in I_in and gd in I_out:
            all_grids[gd] = all_grids[gd] - I_out[gd]
        else:
            continue
    data = {k: v for k, v in all_grids.items() if v > 0}
    # print(len(data))
    # gridbeta = pd.read_csv('gridBeta_100v2.csv')  # 所有网格的贝塔N
    stay_t = get_hourStay(day, t)
    df4 = pd.merge(df_grids, stay_t, on='grid', how='inner')
    # 所有网格N
    df4 = df4[df4['grid'].isin(data.keys())]
    # print(df4.shape)
    df4 = df4.fillna(0)

    del stay_t
    gc.collect()

    # 总增加的感染人数
    betaIiDict = {}
    rdd = random.random()
    for ii in df4.index.tolist():
        name = df4.loc[ii, 'grid']
        beta = float(df4.loc[ii, 'beta'])
        p_stay = df4.loc[ii, 'pop_stay']
        cases = all_grids[name]
        if cases > 0 and p_stay > 0:
            namda = cases * beta / p_stay
            BP_i = binom.pmf(1, p_stay, namda)
            if BP_i > rdd:
                if name in betaIjiDict:
                    betaIiDict[name] = betaIjiDict[name] + 1
                else:
                    betaIiDict[name] = 1
            else:
                continue
        else:
            continue

    del df4
    gc.collect()

    result = pd.DataFrame(data.items(), columns=['grid', 'cases'])

    # t时刻增加的感染人数
    if betaIiDict:
        pd.DataFrame(betaIiDict.items()).to_csv('CTI_%d_I%d.csv' % (day, t), header=['grid', 'infections'],
                                                index=False)

    return result


if __name__ == "__main__":
    df = pd.read_excel('grids_cases13-15edits.xlsx')
    df_t = df.copy()
    for i in range(1, 48):
        print(i, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        df_t = get_risk_s3(i, df_t)