import os

from tqdm import tqdm

from generate_scene import Scene
from load_backgrounds import backgrounds
from load_pickle import cards

nb_cards_to_generate = 10
save_dir = "data/obj"

if not os.path.isdir(save_dir):
    os.makedirs(save_dir)

for i in tqdm(range(nb_cards_to_generate)):
    bg = backgrounds.get_random()
    img1, card_val1, hulla1, hullb1 = cards.get_random()
    img2, card_val2, hulla2, hullb2 = cards.get_random()

    newimg = Scene(bg, img1, card_val1, hulla1, hullb1, img2, card_val2, hulla2, hullb2)
    newimg.display()
    #newimg.write_files(save_dir)
