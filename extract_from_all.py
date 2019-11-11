import os

from extract_cards_from_video import extract_cards_from_video
from globals import card_suits, card_values

video_dir = "data/video"
extension = "MOV"
imgs_dir = "data/cards"


for suit in card_suits:
    for value in card_values:
        card_name = value + suit
        print(f"Current card: {card_name}")
        video_fn = os.path.join(video_dir, card_name + "." + extension)
        output_dir = os.path.join(imgs_dir, card_name)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        imgs = extract_cards_from_video(video_fn, output_dir, keep_ratio=3, min_focus=3)
        print("Extracted images for %s : %d" % (card_name, len(imgs)))
