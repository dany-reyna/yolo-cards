import os
import pickle
from glob import glob

import cv2

from find_hull import find_hull
from globals import card_suits, card_values, refCornerHL, refCornerLR, cards_pck_path

imgs_dir = "data/cards"

cards = {}
for suit in card_suits:
    for value in card_values:
        card_name = value + suit

        card_dir = os.path.join(imgs_dir, card_name)
        if not os.path.isdir(card_dir):
            print(f"!!! {card_dir} does not exist !!!")
            continue

        cards[card_name] = []
        for f in glob(card_dir + "/*.png"):
            img = cv2.imread(f, cv2.IMREAD_UNCHANGED)

            hullHL = find_hull(img, refCornerHL, debug="no")
            if hullHL is None:
                print(f"File {f} not used.")
                continue

            hullLR = find_hull(img, refCornerLR, debug="no")
            if hullLR is None:
                print(f"File {f} not used.")
                continue

            # We store the image in "rgb" format (we don't need opencv anymore)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            cards[card_name].append((img, hullHL, hullLR))
        print(f"Nb images for {card_name} : {len(cards[card_name])}")

print("Saved in :", cards_pck_path)
pickle.dump(cards, open(cards_pck_path, 'wb'))

cv2.destroyAllWindows()
