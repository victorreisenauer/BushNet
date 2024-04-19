# imports 
import random
import os


# split data into tain, test databatches
def split_data(train_test_split, paths):
    """create test/train data split
    ouput:
    - [tup] train data, test data"""
    random.shuffle(paths)
    i = int(len(paths) * train_test_split)
    return paths[:i], paths[i:]

def find_size_fit(wanted_size, img_size):
    img_width = img_size[0]
    img_height = img_size[1]
    while img_height % wanted_size[0] != 0:
        img_height -= 1
    while img_width % wanted_size[1] != 0:
        img_width -= 1
    return img_width, img_height

def remove_img_ext(img_name):
    return img_name.split('.')[0]

# get image name seperated from previous path
def get_img_name(img_path, ext=True):
    img_name = os.path.split(img_path)[1]
    if ext is False:
        img_name = remove_img_ext(img_name)
    return img_name

# split (4000, 3000) into smaller sub-images
def split_into_subimages(img, wanted_size):
    img_width, img_height = find_size_fit(wanted_size, img.size)
    for i in range(int(img_width / wanted_size[1])):
        x_coord = i * wanted_size[1]
        for j in range(int(img_height / wanted_size[0])):
            y_coord = j * wanted_size[0]
            yield (i+1, j+1), (x_coord, y_coord)

def build_sub_id(img_path, ids):
    return f"{remove_img_ext(img_path)}_{ids[0]}_{ids[1]}.JPG"

# calculate bbox
def calc_box(coords, size):
    coords.extend(list(map(int.__add__, coords, size)))
    return coords

def unpack_point(point):
    return [point.x, point.y, point.width, point.height, point.type]

def adjust_point(point_data, coords):
    """adjusts point objects coordinate values to fit sub-image
    """
    new_coords = list(map(int.__sub__, point_data[:2], coords))
    new_coords.extend(point_data[2:])
    return new_coords

def is_point_in_sub(point_box, sub_box):
    if point_box[0] >= sub_box[0] and point_box[2] <= sub_box[2]:
        if point_box[1] >= sub_box[1] and point_box[3] <= sub_box[3]:
            return True
    else:
        False


"""



# split images to fit image size specifications
sub_ids = []
for img_path in img_paths:
    img_name = get_img_name(img_path)
    img = Image.open(img_path)
    wanted_size = config.meta.IMG_SIZE[::-1] # width, height

    if img.size == wanted_size: 
        print(f"Size of images is '{img.size}'.")
    elif img.size[0] < wanted_size[0] or img.size[1] < wanted_size[1]:
        print("Local images are smaller than wanted size")
    else:
        for ids, coords in split_into_subimages(img, wanted_size):
            sub_box = calc_box([coords[0], coords[1]], [wanted_size[0], wanted_size[1]])
            sub_id = build_sub_id(img_path, ids)
            sub_ids.append(sub_id)
            img_data[sub_id] = []
            print(sub_ids)
            for point in img_data[img_name]:
                point_data = unpack_point(point)
                point_box = calc_box(point_data[:2], point_data[2:4])
                if is_point_in_sub(point_box, sub_box):
                    adj_point_data = adjust_point(point_data, coords)
                    img_data[sub_id].append(adj_point_data)
                #img.crop(tuple(sub_box)).save(sub_id)
        #del(img_paths[img_path])
        break


"""