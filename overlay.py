import numpy as np

import cv2


def overlay_test():
    img1 = cv2.imread("ostrich.jpg")
    img2 = cv2.imread("sloth.jpg")
    width, height, _ = img1.shape
    img2 = cv2.resize(img2, (height, width), interpolation=cv2.INTER_AREA)
    img = np.concatenate((img1, img2), axis=1)
    cv2.imshow(" image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


overlay_test()
