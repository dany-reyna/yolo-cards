import cv2
import numpy as np
import matplotlib.pyplot as plt

from globals import refCard, refCardRot
from helpers import display_img
from measures import cardH, cardW

bord_size = 2  # bord_size alpha=0
alphamask = np.ones((cardH, cardW), dtype=np.uint8) * 255
cv2.rectangle(alphamask, (0, 0), (cardW - 1, cardH - 1), 0, bord_size)
cv2.line(alphamask, (bord_size * 3, 0), (0, bord_size * 3), 0, bord_size)
cv2.line(alphamask, (cardW - bord_size * 3, 0), (cardW, bord_size * 3), 0, bord_size)
cv2.line(alphamask, (0, cardH - bord_size * 3), (bord_size * 3, cardH), 0, bord_size)
cv2.line(alphamask, (cardW - bord_size * 3, cardH), (cardW, cardH - bord_size * 3), 0, bord_size)
plt.figure(figsize=(10, 10))
plt.imshow(alphamask)
plt.show()


def variance_of_laplacian(img):
    """
    Compute the Laplacian of the image and then return the focus
    measure, which is simply the variance of the Laplacian
    Source: A.Rosebrock, https://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/
    """
    return cv2.Laplacian(img, cv2.CV_64F).var()


def extract_card(img, output_path=None, min_focus=120, debug=False):
    imgwarp = None

    # Check the image is not too blurry
    focus = variance_of_laplacian(img)
    if focus < min_focus:
        if debug:
            print("Focus too low :", focus)
        return False, None

    # Convert in gray color
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Noise-reducing and edge-preserving filter
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # Edge extraction
    edge = cv2.Canny(gray, 30, 200)

    # Find the contours in the edged image
    cnts, _ = cv2.findContours(edge.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # We suppose that the contour with largest area corresponds to the contour delimiting the card
    cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]

    # We want to check that 'cnt' is the contour of a rectangular shape
    # First, determine 'box', the minimum area bounding rectangle of 'cnt'
    # Then compare area of 'cnt' and area of 'box'
    # Both areas sould be very close
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    areaCnt = cv2.contourArea(cnt)
    areaBox = cv2.contourArea(box)
    valid = areaCnt / areaBox > 0.95

    if not valid:
        return False, None

    # We want transform the zone inside the contour into the reference rectangle of dimensions (cardW,cardH)
    ((xr, yr), (wr, hr), thetar) = rect
    # Determine 'Mp' the transformation that transforms 'box' into the reference rectangle
    if wr > hr:
        Mp = cv2.getPerspectiveTransform(np.float32(box), refCard)
    else:
        Mp = cv2.getPerspectiveTransform(np.float32(box), refCardRot)
    # Determine the warped image by applying the transformation to the image
    imgwarp = cv2.warpPerspective(img, Mp, (cardW, cardH))
    # Add alpha layer
    imgwarp = cv2.cvtColor(imgwarp, cv2.COLOR_BGR2BGRA)

    # Shape of 'cnt' is (n,1,2), type=int with n = number of points
    # We reshape into (1,n,2), type=float32, before feeding to perspectiveTransform
    cnta = cnt.reshape(1, -1, 2).astype(np.float32)
    # Apply the transformation 'Mp' to the contour
    cntwarp = cv2.perspectiveTransform(cnta, Mp)
    cntwarp = cntwarp.astype(np.int)

    # We build the alpha channel so that we have transparency on the
    # external border of the card
    # First, initialize alpha channel fully transparent
    alpha_channel = np.zeros(imgwarp.shape[:2], dtype=np.uint8)
    # Then fill in the contour to make opaque this zone of the card
    cv2.drawContours(alpha_channel, cntwarp, 0, 255, -1)

    # Apply the alphamask onto the alpha channel to clean it
    alpha_channel = cv2.bitwise_and(alpha_channel, alphamask)

    # Add the alphachannel to the warped image
    imgwarp[:, :, 3] = alpha_channel

    # Save the image to file
    if output_path is not None:
        cv2.imwrite(output_path, imgwarp)

    if debug:
        cv2.imshow("Gray", gray)
        cv2.imshow("Canny", edge)
        edge_bgr = cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(edge_bgr, [box], 0, (0, 0, 255), 3)
        cv2.drawContours(edge_bgr, [cnt], 0, (0, 255, 0), -1)
        cv2.imshow("Contour with biggest area", edge_bgr)
        if valid:
            cv2.imshow("Alphachannel", alpha_channel)
            cv2.imshow("Extracted card", imgwarp)

    return valid, imgwarp


dbg = False
image = cv2.imread("test/scene.png")
display_img(image)
is_valid, card = extract_card(image, "test/extracted_card.png", debug=dbg)
if is_valid:
    display_img(card)
if dbg:
    cv2.waitKey(0)
    cv2.destroyAllWindows()
