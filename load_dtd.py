import pickle
from glob import glob

import matplotlib.image as mpimg

from globals import backgrounds_pck_path

dtd_dir = "dtd/images/"
bg_images = []
for subdir in glob(dtd_dir + "/*"):
    for f in glob(subdir + "/*.jpg"):
        bg_images.append(mpimg.imread(f))
print("Nb of images loaded :", len(bg_images))
print("Saved in :", backgrounds_pck_path)
pickle.dump(bg_images, open(backgrounds_pck_path, 'wb'))
