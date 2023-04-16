# -*- coding: utf-8 -*-

import numpy as np
import os, sys
import csv

#file = sys.argv[1]
file = "regions.csv"

with open(file, newline='', encoding="utf-8-sig") as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
      region, samples, lat_min, lon_min, lat_max, lon_max = row['@region'], int(row['@samples']), float(row['@lat_min']), float(row['@lon_min']), float(row['@lat_max']), float(row['@lon_max'])

      lat = np.random.uniform(low=lat_min, high=lat_max, size=samples).reshape(samples,1)
      lon = np.random.uniform(low=lon_min, high=lon_max, size=samples).reshape(samples,1)
      coor = np.hstack((lat, lon))

      np.savetxt(region+'.csv', coor, delimiter=",", fmt='%.6f', header='@lat,@lon', comments='')
