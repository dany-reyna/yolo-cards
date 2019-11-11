from glob import glob
import random
import cv2

from globals import refCornerHL, refCornerLR
from helpers import display_img

# Run a few times...
imgs_dir = "data/cards"
imgs_paths = glob(imgs_dir + "/*/*.png")
img_path = random.choice(imgs_paths)
img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
display_img(img, polygons=[refCornerHL, refCornerLR])
