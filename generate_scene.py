# Scenario with 2 cards:
# The original image of a card has the shape (cardH,cardW,4)
# We first paste it in a zero image of shape (imgH,imgW,4) at position decalX, decalY
# so that the original image is centered in the zero image
import numpy as np
import imgaug
from imgaug import augmenters as iaa
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from create_voc_xml import create_voc_xml
from globals import imgW, imgH
from helpers import give_me_filename
from load_backgrounds import backgrounds
from load_pickle import cards
from measures import cardW, cardH

decalX = int((imgW - cardW) / 2)
decalY = int((imgH - cardH) / 2)

# Scenario with 3 cards : decal values are different
decalX3 = int(imgW / 2)
decalY3 = int(imgH / 2 - cardH)


def kps_to_polygon(kps):
    """
        Convert imgaug keypoints to shapely polygon
    """
    pts = [(kp.x, kp.y) for kp in kps]
    return Polygon(pts)


def hull_to_kps(hull, decalX=decalX, decalY=decalY):
    """
        Convert hull to imgaug keypoints
    """
    # hull is a cv2.Contour, shape : Nx1x2
    kps = [imgaug.Keypoint(x=p[0] + decalX, y=p[1] + decalY) for p in hull.reshape(-1, 2)]
    kps = imgaug.KeypointsOnImage(kps, shape=(imgH, imgW, 3))
    return kps


def kps_to_BB(kps):
    """
        Determine imgaug bounding box from imgaug keypoints
    """
    extend = 3  # To make the bounding box a little bit bigger
    kpsx = [kp.x for kp in kps.keypoints]
    minx = max(0, int(min(kpsx) - extend))
    maxx = min(imgW, int(max(kpsx) + extend))
    kpsy = [kp.y for kp in kps.keypoints]
    miny = max(0, int(min(kpsy) - extend))
    maxy = min(imgH, int(max(kpsy) + extend))
    if minx == maxx or miny == maxy:
        return None
    else:
        return imgaug.BoundingBox(x1=minx, y1=miny, x2=maxx, y2=maxy)


# imgaug keypoints of the bounding box of a whole card
cardKP = imgaug.KeypointsOnImage([
    imgaug.Keypoint(x=decalX, y=decalY),
    imgaug.Keypoint(x=decalX + cardW, y=decalY),
    imgaug.Keypoint(x=decalX + cardW, y=decalY + cardH),
    imgaug.Keypoint(x=decalX, y=decalY + cardH)
], shape=(imgH, imgW, 3))

# imgaug transformation for one card in scenario with 2 cards
transform_1card = iaa.Sequential([
    iaa.Affine(scale=[0.65, 1]),
    iaa.Affine(rotate=(-180, 180)),
    iaa.Affine(translate_percent={"x": (-0.25, 0.25), "y": (-0.25, 0.25)}),
])

# For the 3 cards scenario, we use 3 imgaug transforms, the first 2 are for individual cards,
# and the third one for the group of 3 cards
trans_rot1 = iaa.Sequential([
    iaa.Affine(translate_px={"x": (10, 20)}),
    iaa.Affine(rotate=(22, 30))
])
trans_rot2 = iaa.Sequential([
    iaa.Affine(translate_px={"x": (0, 5)}),
    iaa.Affine(rotate=(10, 15))
])
transform_3cards = iaa.Sequential([
    iaa.Affine(translate_px={"x": decalX - decalX3, "y": decalY - decalY3}),
    iaa.Affine(scale=[0.65, 1]),
    iaa.Affine(rotate=(-180, 180)),
    iaa.Affine(translate_percent={"x": (-0.2, 0.2), "y": (-0.2, 0.2)})
])

# imgaug transformation for the background
scaleBg = iaa.Resize({"height": imgH, "width": imgW})


def augment(img, list_kps, seq, restart=True):
    """
        Apply augmentation 'seq' to image 'img' and keypoints 'list_kps'
        If restart is False, the augmentation has been made deterministic outside
        the function (used for 3 cards scenario)
    """
    # Make sequence deterministic
    while True:
        if restart:
            myseq = seq.to_deterministic()
        else:
            myseq = seq
        # Augment image, keypoints and bbs
        img_aug = myseq.augment_images([img])[0]
        list_kps_aug = [myseq.augment_keypoints([kp])[0] for kp in list_kps]
        list_bbs = [kps_to_BB(list_kps_aug[1]), kps_to_BB(list_kps_aug[2])]
        valid = True
        # Check the card bounding box stays inside the image
        for bb in list_bbs:
            if bb is None or int(round(bb.x2)) >= imgW or int(round(bb.y2)) >= imgH \
                    or int(bb.x1) <= 0 or int(bb.y1) <= 0:
                valid = False
                break
        if valid:
            break
        elif not restart:
            img_aug = None
            break

    return img_aug, list_kps_aug, list_bbs


class BBA:  # Bounding box + annotations
    def __init__(self, bb, classname):
        self.x1 = int(round(bb.x1))
        self.y1 = int(round(bb.y1))
        self.x2 = int(round(bb.x2))
        self.y2 = int(round(bb.y2))
        self.classname = classname


class Scene:
    def __init__(self, bg, img1, class1, hulla1, hullb1, img2, class2, hulla2, hullb2, img3=None, class3=None,
                 hulla3=None, hullb3=None):
        if img3 is not None:
            self.create3CardsScene(bg, img1, class1, hulla1, hullb1, img2, class2, hulla2, hullb2, img3, class3, hulla3,
                                   hullb3)
        else:
            self.create2CardsScene(bg, img1, class1, hulla1, hullb1, img2, class2, hulla2, hullb2)

    def create2CardsScene(self, bg, img1, class1, hulla1, hullb1, img2, class2, hulla2, hullb2):
        kpsa1 = hull_to_kps(hulla1)
        kpsb1 = hull_to_kps(hullb1)
        kpsa2 = hull_to_kps(hulla2)
        kpsb2 = hull_to_kps(hullb2)

        # Randomly transform 1st card
        self.img1 = np.zeros((imgH, imgW, 4), dtype=np.uint8)
        self.img1[decalY:decalY + cardH, decalX:decalX + cardW, :] = img1
        self.img1, self.lkps1, self.bbs1 = augment(self.img1, [cardKP, kpsa1, kpsb1], transform_1card)

        # Randomly transform 2nd card. We want that card 2 does not partially cover a corner of 1 card.
        # If so, we apply a new random transform to card 2
        while True:
            self.listbba = []
            self.img2 = np.zeros((imgH, imgW, 4), dtype=np.uint8)
            self.img2[decalY:decalY + cardH, decalX:decalX + cardW, :] = img2
            self.img2, self.lkps2, self.bbs2 = augment(self.img2, [cardKP, kpsa2, kpsb2], transform_1card)

            # mainPoly2: shapely polygon of card 2
            mainPoly2 = kps_to_polygon(self.lkps2[0].keypoints[0:4])
            invalid = False
            intersect_ratio = 0.1
            for i in range(1, 3):
                # smallPoly1: shapely polygon of one of the hull of card 1
                smallPoly1 = kps_to_polygon(self.lkps1[i].keypoints[:])
                a = smallPoly1.area
                # We calculate area of the intersection of card 1 corner with card 2
                intersect = mainPoly2.intersection(smallPoly1)
                ai = intersect.area
                # If intersection area is small enough, we accept card 2
                if (a - ai) / a > 1 - intersect_ratio:
                    self.listbba.append(BBA(self.bbs1[i - 1], class1))
                # If intersectio area is not small, but also not big enough, we want apply new transform to card 2
                elif (a - ai) / a > intersect_ratio:
                    invalid = True
                    break

            if not invalid:
                break

        self.class1 = class1
        self.class2 = class2
        for bb in self.bbs2:
            self.listbba.append(BBA(bb, class2))
        # Construct final image of the scene by superimposing: bg, img1 and img2
        self.bg = scaleBg.augment_image(bg)
        mask1 = self.img1[:, :, 3]
        self.mask1 = np.stack([mask1] * 3, -1)
        self.final = np.where(self.mask1, self.img1[:, :, 0:3], self.bg)
        mask2 = self.img2[:, :, 3]
        self.mask2 = np.stack([mask2] * 3, -1)
        self.final = np.where(self.mask2, self.img2[:, :, 0:3], self.final)

    def create3CardsScene(self, bg,
                          img1, class1, hulla1, hullb1,
                          img2, class2, hulla2, hullb2,
                          img3, class3, hulla3, hullb3):

        kpsa1 = hull_to_kps(hulla1, decalX3, decalY3)
        kpsb1 = hull_to_kps(hullb1, decalX3, decalY3)
        kpsa2 = hull_to_kps(hulla2, decalX3, decalY3)
        kpsb2 = hull_to_kps(hullb2, decalX3, decalY3)
        kpsa3 = hull_to_kps(hulla3, decalX3, decalY3)
        kpsb3 = hull_to_kps(hullb3, decalX3, decalY3)
        self.img3 = np.zeros((imgH, imgW, 4), dtype=np.uint8)
        self.img3[decalY3:decalY3 + cardH, decalX3:decalX3 + cardW, :] = img3
        self.img3, self.lkps3, self.bbs3 = augment(self.img3, [cardKP, kpsa3, kpsb3], trans_rot1)
        self.img2 = np.zeros((imgH, imgW, 4), dtype=np.uint8)
        self.img2[decalY3:decalY3 + cardH, decalX3:decalX3 + cardW, :] = img2
        self.img2, self.lkps2, self.bbs2 = augment(self.img2, [cardKP, kpsa2, kpsb2], trans_rot2)
        self.img1 = np.zeros((imgH, imgW, 4), dtype=np.uint8)
        self.img1[decalY3:decalY3 + cardH, decalX3:decalX3 + cardW, :] = img1

        while True:
            det_transform_3cards = transform_3cards.to_deterministic()
            _img3, _lkps3, self.bbs3 = augment(self.img3, self.lkps3, det_transform_3cards, False)
            if _img3 is None:
                continue
            _img2, _lkps2, self.bbs2 = augment(self.img2, self.lkps2, det_transform_3cards, False)
            if _img2 is None:
                continue
            _img1, self.lkps1, self.bbs1 = augment(self.img1, [cardKP, kpsa1, kpsb1], det_transform_3cards, False)
            if _img1 is None:
                continue
            break
        self.img3 = _img3
        self.lkps3 = _lkps3
        self.img2 = _img2
        self.lkps2 = _lkps2
        self.img1 = _img1

        self.class1 = class1
        self.class2 = class2
        self.class3 = class3
        self.listbba = [BBA(self.bbs1[0], class1), BBA(self.bbs2[0], class2), BBA(self.bbs3[0], class3),
                        BBA(self.bbs3[1], class3)]

        # Construct final image of the scene by superimposing: bg, img1, img2 and img3
        self.bg = scaleBg.augment_image(bg)
        mask1 = self.img1[:, :, 3]
        self.mask1 = np.stack([mask1] * 3, -1)
        self.final = np.where(self.mask1, self.img1[:, :, 0:3], self.bg)
        mask2 = self.img2[:, :, 3]
        self.mask2 = np.stack([mask2] * 3, -1)
        self.final = np.where(self.mask2, self.img2[:, :, 0:3], self.final)
        mask3 = self.img3[:, :, 3]
        self.mask3 = np.stack([mask3] * 3, -1)
        self.final = np.where(self.mask3, self.img3[:, :, 0:3], self.final)

    def display(self):
        fig, ax = plt.subplots(1, figsize=(8, 8))
        ax.imshow(self.final)
        for bb in self.listbba:
            rect = patches.Rectangle((bb.x1, bb.y1), bb.x2 - bb.x1, bb.y2 - bb.y1, linewidth=1, edgecolor='b',
                                     facecolor='none')
            ax.add_patch(rect)
        plt.show()

    def res(self):
        return self.final

    def write_files(self, save_dir, display=False):
        jpg_path, xml_path = give_me_filename(save_dir, ["jpg", "xml"])
        plt.imsave(jpg_path, self.final)
        if display:
            print("New image saved in", jpg_path)
        create_voc_xml(xml_path, jpg_path, self.listbba, display=display)


if __name__ == '__main__':
    # Test generation of a scene with 2 cards
    bg = backgrounds.get_random()
    img1, card_val1, hulla1, hullb1 = cards.get_random()
    img2, card_val2, hulla2, hullb2 = cards.get_random()

    newimg = Scene(bg, img1, card_val1, hulla1, hullb1, img2, card_val2, hulla2, hullb2)
    newimg.display()

    # Test generation of a scene with 3 cards
    bg = backgrounds.get_random()
    img1, card_val1, hulla1, hullb1 = cards.get_random()
    img2, card_val2, hulla2, hullb2 = cards.get_random()
    img3, card_val3, hulla3, hullb3 = cards.get_random()

    newimg = Scene(bg, img1, card_val1, hulla1, hullb1, img2, card_val2, hulla2, hullb2, img3, card_val3, hulla3,
                   hullb3)
    newimg.display()
