import os

import numpy as np

from measures import cardW, cardH, cornerXmin, cornerYmin, cornerXmax, cornerYmax

data_dir = "data"  # Directory that will contain all kinds of data (the data we download and the data we generate)

if not os.path.isdir(data_dir):
    os.makedirs(data_dir)

card_suits = ['s', 'h', 'd', 'c']
card_values = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

# Pickle file containing the background images from the DTD
backgrounds_pck_path = data_dir + "/backgrounds.pck"

# Pickle file containing the card images
cards_pck_path = data_dir + "/cards.pck"

# imgW, imgH: dimensions of the generated dataset images
imgW = 720
imgH = 720

refCard = np.array([[0, 0], [cardW, 0], [cardW, cardH], [0, cardH]], dtype=np.float32)
refCardRot = np.array([[cardW, 0], [cardW, cardH], [0, cardH], [0, 0]], dtype=np.float32)
refCornerHL = np.array(
    [[cornerXmin, cornerYmin], [cornerXmax, cornerYmin], [cornerXmax, cornerYmax], [cornerXmin, cornerYmax]],
    dtype=np.float32)
refCornerLR = np.array([[cardW - cornerXmax, cardH - cornerYmax], [cardW - cornerXmin, cardH - cornerYmax],
                        [cardW - cornerXmin, cardH - cornerYmin], [cardW - cornerXmax, cardH - cornerYmin]],
                       dtype=np.float32)
refCorners = np.array([refCornerHL, refCornerLR])
