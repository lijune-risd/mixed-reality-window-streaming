import cv2
import mediapipe as mp
import numpy as np
import math
import os


# img1 = cv2.imread("ostrich.jpg")
# img2 = cv2.imread("sloth.jpg")
# height, width, _ = img1.shape
# img2 = cv2.resize(img2, (width//2, height//2), interpolation=cv2.INTER_AREA)
# image = img1
# # img = np.concatenate((img1, img2), axis=1)
# img1[0:height//2, 0:width//2] = img2
# cv2.imshow(" image", img1)
# cv2.waitKey(0)
# cv2.destroyAllWindows()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~background video~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def replace_background(fg, bg):
    # bg_image = cv2.imread("sloth.jpg")
    # bg_image = cv2.imread(fg_path)
    # frame = cv2.imread(bg_path)
    bg_image = bg
    frame = fg

    # initialize mediapipe
    mp_selfie_segmentation = mp.solutions.selfie_segmentation
    selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(
            model_selection=1)


    RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # get the result
    results = selfie_segmentation.process(RGB)
    # extract segmented mask
    mask = results.segmentation_mask
    # return mask

    # show outputs
    # cv2.imshow("mask", mask)
    # cv2.imshow("Frame", frame)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # it returns true or false where the condition applies in the mask
    condition = np.stack(
            (results.segmentation_mask,) * 3, axis=-1) > 0.5
    height, width = frame.shape[:2]
    # resize the background image to the same size of the original frame
    bg_image = cv2.resize(bg_image, (width, height))
    # combine frame and background image using the condition
    output_image = np.where(condition, frame, bg_image)
    return output_image
