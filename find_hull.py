from glob import glob
import random

import cv2
import numpy as np
import matplotlib.pyplot as plt

from globals import refCornerHL, refCornerLR
from helpers import display_img


def find_hull(img, corner=refCornerHL, debug="no"):
    """
        Find in the zone 'corner' of image 'img' and return, the convex hull delimiting
        the value and suit symbols
        'corner' (shape (4,2)) is an array of 4 points delimiting a rectangular zone,
        takes one of the 2 possible values : refCornerHL or refCornerLR
        debug=
    """

    kernel = np.ones((3, 3), np.uint8)
    corner = corner.astype(np.int)

    # We will focus on the zone of 'img' delimited by 'corner'
    x1 = int(corner[0][0])
    y1 = int(corner[0][1])
    x2 = int(corner[2][0])
    y2 = int(corner[2][1])
    w = x2 - x1
    h = y2 - y1
    zone = img[y1:y2, x1:x2].copy()

    strange_cnt = np.zeros_like(zone)
    gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
    thld = cv2.Canny(gray, 30, 200)
    thld = cv2.dilate(thld, kernel, iterations=1)
    if debug != "no":
        cv2.imshow("thld", thld)
        plt.show()

    # Find the contours
    contours, _ = cv2.findContours(thld.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = 30  # We will reject contours with small area. TWEAK, 'zoom' dependant
    min_solidity = 0.3  # Reject contours with a low solidity. TWEAK

    concat_contour = None  # We will aggregate in 'concat_contour' the contours that we want to keep

    ok = True
    for c in contours:
        area = cv2.contourArea(c)

        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area
        # Determine the center of gravity (cx,cy) of the contour
        M = cv2.moments(c)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        # abs(w/2-cx)<w*0.3 and abs(h/2-cy)<h*0.4 : TWEAK, the idea here is to
        # keep only the contours which are closed to the center of the zone
        if area >= min_area and abs(w / 2 - cx) < w * 0.3 and abs(h / 2 - cy) < h * 0.4 and solidity > min_solidity:
            if debug != "no":
                cv2.drawContours(zone, [c], 0, (255, 0, 0), -1)
            if concat_contour is None:
                concat_contour = c
            else:
                concat_contour = np.concatenate((concat_contour, c))
        if debug != "no" and solidity <= min_solidity:
            print("Solidity", solidity)
            cv2.drawContours(strange_cnt, [c], 0, 255, 2)
            cv2.imshow("Strange contours", strange_cnt)
            plt.show()

    if concat_contour is not None:
        # At this point, we suppose that 'concat_contour' contains only the
        # contours corresponding the value and suit symbols
        # We can now determine the hull
        hull = cv2.convexHull(concat_contour)
        hull_area = cv2.contourArea(hull)
        # If the area of the hull is to small or too big, there may be a problem
        min_hull_area = 940  # TWEAK, deck and 'zoom' dependant
        max_hull_area = 2120  # TWEAK, deck and 'zoom' dependant
        if hull_area < min_hull_area or hull_area > max_hull_area:
            ok = False
            if debug != "no":
                print("Hull area=", hull_area, "too large or too small")
        # So far, the coordinates of the hull are relative to 'zone'
        # We need the coordinates relative to the image -> 'hull_in_img'
        hull_in_img = hull + corner[0]
    else:
        ok = False

    if debug != "no":
        if concat_contour is not None:
            cv2.drawContours(zone, [hull], 0, (0, 255, 0), 1)
            cv2.drawContours(img, [hull_in_img], 0, (0, 255, 0), 1)
        cv2.imshow("Zone", zone)
        plt.show()
        cv2.imshow("Image", img)
        plt.show()
        if ok and debug != "pause_always":
            key = cv2.waitKey(1)
        else:
            key = cv2.waitKey(0)
        if key == 27:
            return None
    if not ok:
        return None

    return hull_in_img


if __name__ == '__main__':
    # Test find_hull on a random card image
    # debug = "no" or "pause_always" or "pause_on_pb"
    # If debug!="no", you may have to press a key to continue execution after pause
    debug = "no"
    imgs_dir = "data/cards"
    imgs_paths = glob(imgs_dir + "/*/*.png")
    img_path = random.choice(imgs_paths)
    print(img_path)
    image = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    hullHL = find_hull(image, refCornerHL, debug=debug)
    hullLR = find_hull(image, refCornerLR, debug=debug)
    display_img(image, [refCornerHL, refCornerLR, hullHL, hullLR])

    if debug != "no":
        cv2.destroyAllWindows()
