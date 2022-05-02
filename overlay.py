import cv2
import mediapipe as mp
import numpy as np
import math
import os


def replace_background(fg, bg):
    # bg_image = cv2.imread("sloth.jpg")
    # bg_image = cv2.imread(fg_path)
    # frame = cv2.imread(bg_path)
    bg_image = bg
    frame = fg

    # initialize mediapipe
    mp_selfie_segmentation = mp.solutions.selfie_segmentation
    # selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(
    #         model_selection=1)
    selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation()

    RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # get the result
    results = selfie_segmentation.process(RGB)
    # print
    # cv2.imshow("results", results)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # extract segmented mask

    mask = results.segmentation_mask
    mask = cv2.GaussianBlur(mask, (33, 33), 0)
    # return mask

    # it returns true or false where the condition applies in the mask
    condition = np.stack(
        (mask,) * 3, axis=-1) > 0.6
    height, width = frame.shape[:2]
    # resize the background image to the same size of the original frame
    bg_image = cv2.resize(bg_image, (width, height))
    # bg_image = cv2.GaussianBlur(bg_image, (55, 55), 0)
    # combine frame and background image using the condition
    output_image = np.where(condition, frame, bg_image)
    return output_image



    
# # # img1 = cv2.imread("ostrich.jpg")
# # # img2 = cv2.imread("sloth.jpg")
# # # height, width, _ = img1.shape
# # # img2 = cv2.resize(img2, (width//2, height//2), interpolation=cv2.INTER_AREA)
# # # image = img1
# # # # img = np.concatenate((img1, img2), axis=1)
# # # img1[0:height//2, 0:width//2] = img2
# # # cv2.imshow(" image", img1)
# # # cv2.waitKey(0)
# # # cv2.destroyAllWindows()


# # # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~background video~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# # def replace_background(fg, bg):
# #     # bg_image = cv2.imread("sloth.jpg")
# #     # bg_image = cv2.imread(fg_path)
# #     # frame = cv2.imread(bg_path)
# #     bg_image = bg
# #     frame = fg

# #     # initialize mediapipe
# #     mp_selfie_segmentation = mp.solutions.selfie_segmentation
# #     selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation(
# #             model_selection=1)


# #     RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# #     # get the result
# #     results = selfie_segmentation.process(RGB)
# #     # extract segmented mask
# #     mask = results.segmentation_mask
# #     # return mask

# #     # show outputs
# #     # cv2.imshow("mask", mask)
# #     # cv2.imshow("Frame", frame)
# #     # cv2.waitKey(0)
# #     # cv2.destroyAllWindows()

# #     # it returns true or false where the condition applies in the mask
# #     condition = np.stack(
# #             (results.segmentation_mask,) * 3, axis=-1) > 0.5
# #     height, width = frame.shape[:2]
# #     # resize the background image to the same size of the original frame
# #     bg_image = cv2.resize(bg_image, (width, height))
# #     # combine frame and background image using the condition
# #     output_image = np.where(condition, frame, bg_image)
# #     return output_image


# # #  test mask
# # bg_image = cv2.imread("ostrich.jpg")
# # frame = cv2.imread("sloth.jpg")
# # mask = replace_background(bg_image, frame)
# # cv2.imshow("mask", mask)
# # cv2.imshow("Frame", frame)
# # cv2.waitKey(0)
# # cv2.destroyAllWindows()
# # # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~blur background~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# # mp_drawing = mp.solutions.drawing_utils
# mp_selfie_segmentation = mp.solutions.selfie_segmentation

# # IMAGE_FILES = ["ostrich.jpg", "sloth.jpg"]
# # DESIRED_HEIGHT = 480
# # DESIRED_WIDTH = 480


# # def resize_and_show(image):
# #     h, w = image.shape[:2]
# #     if h < w:
# #         img = cv2.resize(
# #             image, (DESIRED_WIDTH, math.floor(h/(w/DESIRED_WIDTH))))
# #     else:
# #         img = cv2.resize(
# #             image, (math.floor(w/(h/DESIRED_HEIGHT)), DESIRED_HEIGHT))
# #     cv2.imshow(" image", img)


# # # Read images with OpenCV.

# # # Preview the images.
# # for name, image in images.items():
# #     print(name)
# #     resize_and_show(image)


# # IMAGE_FILES = ["ostrich.jpg", "sloth.jpg"]
# # images = {name: cv2.imread(name) for name in IMAGE_FILES}
# # DESIRED_HEIGHT = 480
# # DESIRED_WIDTH = 480
# # fg = cv2.imread("ostrich.jpg")
# # bg = cv2.imread("sloth.jpg")

# # BG_COLOR = (192, 192, 192)  # gray
# # MASK_COLOR = (255, 255, 255)  # white
# # with mp_selfie_segmentation.SelfieSegmentation(
# #         model_selection=0) as selfie_segmentation:
# #     for idx, file in enumerate(IMAGE_FILES):

# #         img1 = cv2.imread(file)
# #         # img2 = cv2.imread("sloth.jpg")
# #         # height, width, _ = img1.shape
# #         # img2 = cv2.resize(img2, (width, height), interpolation=cv2.INTER_AREA)
# #         image = img1
# #         # img = np.concatenate((img1, img2), axis=1)
# #         # cv2.imshow(" image", img)
# #         # cv2.waitKey(0)
# #         # cv2.destroyAllWindows()
# #         results = selfie_segmentation.process(
# #             cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
# #         condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
# #         # Generate solid color images for showing the output selfie segmentation mask.
# #         print("yo")
# #         fg_image = np.zeros(image.shape, dtype=np.uint8)
# #         fg_image[:] = MASK_COLOR
# #         bg_image = np.zeros(image.shape, dtype=np.uint8)
# #         bg_image[:] = BG_COLOR
# #         output_image = np.where(condition, fg_image, bg_image)
# #         print("hi")
# #         cv2.imwrite('selfie_segmentation_output' +
# #                     str(idx) + '.png', output_image)
# #         cv2.imshow(" image", output_image)
# #         cv2.waitKey(0)
# #         cv2.destroyAllWindows()
#     # resize_and_show(output_image)

# # with mp_selfie_segmentation.SelfieSegmentation() as selfie_segmentation:
# #     for name, image in images.items():
# #         # Convert the BGR image to RGB and process it with MediaPipe Selfie Segmentation.
# #         results = selfie_segmentation.process(
# #             cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

# #         blurred_image = cv2.GaussianBlur(image, (55, 55), 0)
# #         condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
# #         output_image = np.where(condition, image, blurred_image)

# #         print(f'Blurred background of {name}:')
# #         cv2.imshow(" image", output_image)
# #         cv2.waitKey(0)
# #         cv2.destroyAllWindows()
# #         # resize_and_show(output_image)
# IMAGE_FILES = ["ostrich.jpg", "sloth.jpg"]
# images = {name: cv2.imread(name) for name in IMAGE_FILES}
# DESIRED_HEIGHT = 480
# DESIRED_WIDTH = 480
# fg = cv2.imread("ostrich.jpg")
# bg = cv2.imread("sloth.jpg")

# with mp_selfie_segmentation.SelfieSegmentation() as selfie_segmentation:
#     for name, image in images.items():
#         # Convert the BGR image to RGB and process it with MediaPipe Selfie Segmentation.
#         results = selfie_segmentation.process(
#             cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

#         blurred_image = cv2.GaussianBlur(image, (55, 55), 0)
#         condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
#         output_image = np.where(condition, image, blurred_image)

#         print(f'Blurred background of {name}:')
#         cv2.imshow(" image", output_image)
#         cv2.waitKey(0)
#         cv2.destroyAllWindows()
#         # resize_and_show(output_image)
