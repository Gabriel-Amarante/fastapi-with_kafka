import os

# path to fold with .csv files with the coordinates per region
path = "PATH TO /mpmg_streetview_images/coordenadas"

for file in os.listdir(path):
    region = file.split('.')[0]

    os.system("python3 download_data.py " + file + " " + region)
