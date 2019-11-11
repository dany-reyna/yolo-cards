import pickle
import random

import matplotlib.pyplot as plt

from globals import backgrounds_pck_path


class Backgrounds:
    def __init__(self, backgrounds_pck_fn=backgrounds_pck_path):
        self._images = pickle.load(open(backgrounds_pck_fn, 'rb'))
        self._nb_images = len(self._images)
        print("Nb of images loaded :", self._nb_images)

    def get_random(self, display=False):
        bg = self._images[random.randint(0, self._nb_images - 1)]
        if display:
            plt.imshow(bg)
            plt.show()
        return bg


backgrounds = Backgrounds()
if __name__ == '__main__':
    _ = backgrounds.get_random(display=True)
