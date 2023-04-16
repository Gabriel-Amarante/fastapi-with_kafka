import os, sys, urllib
import urllib.request
import urllib.parse
import csv

# the API key is required to authenticate the request
key = "&key=" + "COLOQUE AQUI A SUA KEY DO GOOGLE STREETVIEW"

# Image size up to 640x640
size = "&size=" + "640x640"

# Radius, specified in meters, in which to search for a panorama,
# centered on the given latitude and longitude. Default is 50.
radius = "&radius=" + "50"

# heading indicates the compass heading of the camera.
# From 0 to 360 (both values indicating North,
# with 90 indicating East, and 180 South).
angles = [0, 45, 90, 135]

# link base for requests
# image size set to 640 x 640 pixels
base_metadata = "https://maps.googleapis.com/maps/api/streetview/metadata?" + size + radius + key + "&location="
base_street = "https://maps.googleapis.com/maps/api/streetview?" + size + radius + key + "&location="
base_aerial = "https://maps.googleapis.com/maps/api/staticmap?" + size + radius + key + "&zoom=19&maptype=satellite&center="

# sys.argv[1] - refers to .csv file with coordinates
# sys.argv[2] - refers to the name for the class of the images requested
class_f = sys.argv[2]

outf_street = os.path.join("../mpmg_google_images/tst_cv_clean/street", class_f)
outf_aerial = os.path.join("../mpmg_google_images/tst_cv_clean/aerial", class_f)
outf_metadata = os.path.join("../mpmg_google_images/tst_cv_clean/metadata", class_f)

if not os.path.exists(outf_metadata):
    os.mkdir(outf_metadata)
if not os.path.exists(outf_aerial):
    os.mkdir(outf_aerial)
if not os.path.exists(outf_street):
    os.mkdir(outf_street)

# fetched_data are data already available on the directory
fetched_data = [x.split('.')[0] for x in os.listdir(outf_metadata)]

with open(sys.argv[1], newline='', encoding="utf-8-sig") as csvfile:
    spamreader = csv.DictReader(csvfile)
    for row in spamreader:
        # obtaining one image per angle defined initially
        for angle in angles:
            heading = "&heading=" + str(angle)

            # url do dado a ser importado e seus parametros
            MyUrlMD = base_metadata + urllib.parse.quote_plus(row['@lat'] + ',' + row['@lon']) + heading #added url encoding
            all_data = True
            try:
                f = urllib.request.urlopen(MyUrlMD)
            except:
                continue

            # t é o json com o metadado em formato de string
            # a é o metadado em formato de dicionario
            t = f.read().decode('utf-8')
            a = eval(t)

            if not a['status'] == "OK":
                continue

            if a['pano_id'] + "_" + str(angle) in fetched_data or ('CAoS' in a['pano_id']):
                continue
            else:
                fetched_data.append(a['pano_id'])

            basename = a['pano_id'] + "_" + str(angle)
            file_img_street = os.path.join(outf_street, basename + ".jpg")
            file_img_aerial = os.path.join(outf_aerial, basename + ".png")
            file_meta = os.path.join(outf_metadata, basename + ".json")

            meta = open(file_meta, "wb")
            meta.write(t.encode('utf-8'))

            point = row['@lat'] + ',' + row['@lon']

            try:
                base = base_street + urllib.parse.quote_plus(point) + heading
                urllib.request.urlretrieve(base, file_img_street)
            except:
                all_data = False

            try:
                base = base_aerial + urllib.parse.quote_plus(point) + heading
                urllib.request.urlretrieve(base, file_img_aerial)
            except:
                all_data = False

            if not all_data:
                if os.path.exists(file_meta):
                    os.remove(file_meta)
                if os.path.exists(file_img_street):
                    os.remove(file_img_street)
                if os.path.exists(file_img_aerial):
                    os.remove(file_img_aerial)
