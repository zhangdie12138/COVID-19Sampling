# -*- coding:utf-8 -*-

from osgeo import ogr
import pandas as pd
import multiprocessing as mp
import numpy as np


def poi_county_senc(item):
    ds = ogr.Open('BJ_POI.shp', False)  # False - read only, True - read/write
    layer_copy = ds.GetLayer(0)
    layer_copy.SetSpatialFilter(None)
    layer_copy.SetAttributeFilter(None)
    (idd, wkt) = item

    geom = ogr.CreateGeometryFromWkt(wkt)
    layer_copy.SetSpatialFilter(geom)

    num = layer_copy.GetFeatureCount()

    feature = layer_copy.GetNextFeature()
    risks2 = []
    while feature is not None:
        risk = feature.GetField('risk')
        risks2.append(risk)
        feature = layer_copy.GetNextFeature()
    if risks2:
        risk3 = pd.DataFrame(risks2, columns=['risk'])
        class_risk = risk3['risk'].groupby(risk3['risk']).agg('sum')
        gridIdRisk = np.power(np.sum(np.power(class_risk, 0.4)), 5 / 3)
        poirisk = [idd, gridIdRisk, num]
    else:
        poirisk = [idd, 0, 0]
    ds.Destroy()
    return poirisk


if __name__ == "__main__":
    # get geomlist
    ds_geo = ogr.Open('CommunityPolygon.shp', False)  # False - read only, True - read/write
    layer_geo = ds_geo.GetLayer(0)
    geomlist = []
    feature_geo = layer_geo.GetNextFeature()
    while feature_geo is not None:
        geom = feature_geo.GetGeometryRef().ExportToWkt()
        idd = feature_geo.GetField('Community_id')
        geomlist.append((idd, geom))
        feature_geo = layer_geo.GetNextFeature()
    ds_geo.Destroy()
    # pool
    p = mp.Pool(processes=4)
    poiNum = p.map(poi_county_senc, geomlist)

    # output
    milk = pd.DataFrame(poiNum)
    milk.to_csv('Community_POI_diversity.csv', index=False, header=False)