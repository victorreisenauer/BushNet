"""configuration script for paths"""

# import the necessary packages
import os


# initialize the base path for the dataset
BASE_PATH = "data"

# build the path to the images folders
IMAGES_PATH = os.path.sep.join([BASE_PATH, "images"])

# build the path to the  training and test .csv files
# needed as input to retina net
TRAIN_CSV = os.path.sep.join([BASE_PATH, "train.csv"])
TEST_CSV = os.path.sep.join([BASE_PATH, "test.csv"])

# build the path to the output classes .csv files
# classes.csv is afile with all unique class labels in the dataset 
# with index assignments (starting from 0 and ignoring the background)
CLASSES_CSV = os.path.sep.join([BASE_PATH, "classes.csv"])

# build path to pretrained models
PRE_MODELS = os.path.sep.join([BASE_PATH, "pretrained_models"])

# build path to output folder 
# all objects predicted on each image by model will be stored here
PREDICTIONS = os.path.sep.join([BASE_PATH, "predictions"])

# folder to store snapshots of model after each training epoch
SNAPSHOTS = "snapshots"

# folder to tensorboard visualization files
TENSORBOARD = "tensorboard"

# folder to logs
LOGS = "logs"




