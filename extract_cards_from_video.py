import os

import cv2

from extract_card import extract_card
from helpers import give_me_filename


def extract_cards_from_video(video_path, output_dir=None, keep_ratio=5, min_focus=120, debug=False):
    """
        Extract cards from media file 'video_path'
        If 'output_dir' is specified, the cards are saved in 'output_dir'.
        One file per card with a random file name
        Because 2 consecutive frames are probably very similar, we don't use every frame of the video,
        but only one every 'keep_ratio' frames

        Returns list of extracted images
    """
    if not os.path.isfile(video_path):
        print(f"Video file {video_path} does not exist !!!")
        return -1, []
    if output_dir is not None and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cap = cv2.VideoCapture(video_path)

    frame_nb = 0
    imgs_list = []
    while True:
        ret, img = cap.read()
        if not ret:
            break
        # Work on every 'keep_ratio' frames
        if frame_nb % keep_ratio == 0:
            if output_dir is not None:
                output_path = give_me_filename(output_dir, "png")
            else:
                output_path = None
            valid, card_img = extract_card(img, output_path, min_focus=min_focus, debug=debug)
            if debug:
                k = cv2.waitKey(1)
                if k == 27:
                    break
            if valid:
                imgs_list.append(card_img)
        frame_nb += 1

    if debug:
        cap.release()
        cv2.destroyAllWindows()

    return imgs_list


if __name__ == '__main__':
    # Test card extraction from a video
    imgs = extract_cards_from_video("test/2c.avi", output_dir="test/2c", debug=True)
    print("Nb images extracted:", len(imgs))
