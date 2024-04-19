# import the necessary packages
from config import paths as con_paths
from config import meta as con_meta
from utils.db import get_db, get_types, save_all_points, load_all_points
from utils.data import split_data
import csv
import os
import sys
from PIL import Image, ImageDraw


def resize_images(IMAGES):
    for i in os.listdir(IMAGES):
        p = os.path.join(IMAGES, i)

        try:
            with Image.open(p) as im:
                if im.size != (4000, 3000):
                    im.thumbnail((4000, 3000))
                    im.save(p)
        except Exception as e:
            print(i, e)


def draw_box(image_obj, coords, obj_type, color):
    
    draw = ImageDraw.Draw(image_obj, mode='RGB')
    draw.rectangle((coords[0], coords[1], coords[2], coords[3]), width=5, outline=color)
    draw.text(coords[0:2], obj_type)


# Create easy variable names for paths
train_csv = con_paths.TRAIN_CSV
test_csv = con_paths.TEST_CSV
classes_csv = con_paths.CLASSES_CSV 

tracked_objs = ['animals']


# get all local image paths
#resize_images(con_paths.IMAGES_PATH)
local_img = os.listdir(con_paths.IMAGES_PATH)

# log into data server
get_db(host="peregrine.hndrk.xyz", user="read",
        password="xFpXfqqsprKK3dHLhK7pVgqFgkCkkT",
        database="label", port=3306)


# pull data of labelled images from server 
print("[INFO] Fetching data from server. Please wait...")
save_all_points("./image_data.json", average=True)

# load data
img_data = {}
for path, points in load_all_points("./test.json", unpacked=False):
    img_data[path] = points



# create list of image names that are both locally stored and image labels received from server
img_paths = [os.path.sep.join(['data', 'images', img]) for img in img_data.keys() if img in local_img]

print(f"[INFO] '{len(img_data.keys())}' image labels received from server.")
print(f"[INFO] '{len(img_paths)}' images are matching and used as dataset.")

# construct training and testing splits from img_paths
train_image_paths, test_image_paths = split_data(con_meta.TRAIN_TEST_SPLIT, img_paths)


# create a list of datasets to build
datasets = [("train", train_image_paths, train_csv),
           ("test", test_image_paths, test_csv)]

# get all classes in dataset and create csv file
csvFile = open(classes_csv, "w", newline='')
writer = csv.writer(csvFile)
for i, obj_type in enumerate(tracked_objs, 0):
    writer.writerow([obj_type, i])
csvFile.close()


#  create test.csv, train.csv and classes.csv files with labelled image data
# 1. loop over datasets
for (dType, img_paths, output_csv) in datasets:
    # 2. load the contents
    print("[INFO] creating '{}' set".format(dType))
    print("[INFO] {} total images in '{}' set".format(len(img_paths), dType))

    # 3. open the output csv file
    csvFile = open(output_csv, "w", newline='')
    writer = csv.writer(csvFile)

    # set up counters:
    obj_counter = {}
    for obj in tracked_objs:
        obj_counter[obj] = 0

    # 4. loop over the image paths and point to add data to .csv files
    for img_path in img_paths:

        #print(img_path)
        img_name = os.path.split(img_path)[-1]
        #print("currently looking at: " + str(img_name))

        img_obj = Image.open(img_path)

        
        
        for i in range(len(img_data[img_name])):
            point = img_data[img_name][i]
            if point.type in tracked_objs:

                x_1 = int(point.x)
                y_1 = int(point.y)
                x_2 = int(point.x + point.width)
                y_2 = int(point.y + point.height)
                if x_1 < x_2 and y_1 < y_2:
                    row = [img_name, x_1, y_1, x_2, y_2, point.type]
                    writer.writerow(row)
                    obj_counter[point.type] += 1
    
    print(f"""
    datapoints summary for the {dType} dataset")
    total datapoints: {sum(obj_counter.values())}
    """)

    for obj in tracked_objs:
        print(f"""      {obj}: {obj_counter[obj]} """)

    print("")
    print("")
    csvFile.close()