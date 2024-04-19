# necessary imports
import argparse 
import csv
import sys
from db import load_all_points
from random import random
from PIL import Image, ImageDraw



# buid argparser
def parse_args(args):
    """ Parse the arguments.
    """
    parser = argparse.ArgumentParser(description='Visualize bounding boxes on images')
    parser.add_argument('--image',                help='input name of image or random', default='random')
    parser.add_argument('--folder_path',        help='path to images folder', default='data/images/')
    parser.add_argument('--type',                   help='type', default='json')
    parser.add_argument('--input_path',        help='path to input data file')

    return parser.parse_args(args)

# bulid draw helper function
def draw_box(image_obj, coords, obj_type):
    
    draw = ImageDraw.Draw(image_obj)
    draw.rectangle([int(coords[0]), int(coords[1]), int(coords[0] + coords[2]), int(coords[1] + coords[3])], width=5)
    draw.text(coords[0:2], obj_type)
    

    

# main script
def main(args=None):
    # store csv data in dict - img_name: {coords: [x, y, height, width], class: class}
    if args is None:
        args = sys.argv[1:]
    args = parse_args(args)

    #if args.image == 'random':
        #limit = len(os.listdir(args.folder-path))
        # todo: get random picture to show

    
    if args.type == 'json':
        for name, points in load_all_points(args.input_path, unpacked=True):
            if name == args.image:
                path = args.folder_path + name
                img_obj = Image.open(path)
                for point in points:
                    draw_box(img_obj, point[0:4], point[4])
                img_obj.show()
                print(path)
                #input('Press ENTER to continue...')
    """
            else:
                print('no pic found')
                path = args.folder_path + name
                img_obj = Image.open(path)
                for point in points:
                    draw_box(img_obj, point[0:4], point[4])
                img_obj.show()
                print(path)
                input('Press ENTER to continue...')
    """

    if args.type == 'csv':
        with open(args.input_path, 'r') as in_f:
            reader = csv.reader(in_f)
            for row in reader:
                if row[0] == args.image:
                    for i in range(1,5):
                        row[i] = int(row[i])
                    name = row[0]
                    path = args.folder_path + name
                    img_obj = Image.open(path)
                    draw_box(img_obj, row[1:5], row[5])
            img_obj.show()
            print(path)
            input('Press enter to continue...')


            

if __name__ == "__main__":
    main()

