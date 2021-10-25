# -*- coding:utf-8 -*-

import pandas as pd
import multiprocessing as mp


def get_risk_s3(tt):
    if tt > 23:
        t = tt - 24
        day = 12
    else:
        t = tt
        day = 11

    df_in = pd.read_csv('OD/202006%d%02d-inODMatrix.csv' % (day, t), sep='\t', index_col=False)
    df_out = pd.read_csv('OD/202006%d%02d-outODMatrix.csv' % (day, t), sep='\t', index_col=False)  # 流出矩阵 p*p
    Pji = df_in.iloc[:, 1:].apply(lambda x: x.sum(), axis=1)
    p_in = {}
    for inx, idd in enumerate(df_in['Unnamed: 0'].tolist()):
        p_in[idd] = Pji.iloc[inx]
    Pik = df_out.iloc[:, 1:].apply(lambda x: x.sum(), axis=1)
    p_out = {}
    for inxx, iddd in enumerate(df_out['Unnamed: 0'].tolist()):
        p_out[iddd] = Pik.iloc[inxx]

    all_grids = {}  # 所有网格病例字典
    df_grids = pd.read_excel('grid_id.xlsx')
    pop_dict = {}
    for ii in df_grids.index.tolist():
        pop = df_grids.loc[ii, 'pop']
        pop_dict[df_grids.loc[ii, 'grid']] = pop
    for gid in df_grids['grid'].tolist():
        if gid in p_in and gid in p_out:
            if pop_dict[gid] > 0:
                all_grids[gid] = (p_in[gid] + p_out[gid]) / pop_dict[gid]
            else:
                continue
        else:
            continue

    pd.DataFrame(all_grids.items()).to_csv('HFI_%d_%d.csv' % (day, t), index=False)


if __name__ == "__main__":
    tList = [i for i in range(48)]
    p = mp.Pool(processes=10)
    p.map(get_risk_s3, tList)
    p.close()
    p.join()
