"""Configuration script for metadata"""

# import the necessary packages
import os
import config.paths


# define the default training/testing split
# by default 75% of images are used for training
TRAIN_TEST_SPLIT = 0.75  

# default pretrained model:

PRE_MODEL = f"--weights {os.path.join(config.paths.PRE_MODELS, 'resnet50_coco_best_v2.1.0.h5')}"

# define the default CNN input image size
IMG_SIZE = (500,500) 

# when image is split into given img_size, at what threshold should 
# objects that are only partly on picture (split objects) be removed
OBJ_THRESHOLD = 0.33

# batch size when training
BATCH_SIZE = "--batch-size 1" 

# steps per batch
n_STEPS = "--steps 5"

# number of epochs
N_EPOCHS = "--epochs 500"

