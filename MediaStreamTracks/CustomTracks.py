
from av import VideoFrame
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
import numpy as np

class WindowTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform, guestTrack):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.guestTrack = guestTrack

    async def recv(self):

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")


        if not self.guestTrack: 
            return frame

        guestFrame = await self.guestTrack.recv()
        guestImg = guestFrame.to_ndarray(format="bgr24")

        try:
            img = np.concatenate((img, guestImg), axis=1)
        except Exception as e:
            pass


        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame



        #  frame = await self.track.recv()
        #  return frame

class GuestTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform, windowFrontTrack):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.windowFrontTrack = windowFrontTrack

    async def recv(self):

        frame = await self.track.recv()

        if not self.windowFrontTrack: 
            return frame

        #  img = frame.to_ndarray(format="bgr24")
        # strip background from img

        windowFrontFrame = await self.windowFrontTrack.recv()
        windowFrontImg = windowFrontFrame.to_ndarray(format="bgr24")

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")


        #  img = np.concatenate((img, img), axis=1)
        try:
            img = np.concatenate((img, windowFrontImg), axis=1)
        except Exception as e:
            pass


        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


class NoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform

    async def recv(self):

        #  ret, frame2 = vid.read()

        #  https://stackoverflow.com/questions/43665208/how-to-get-the-latest-frame-from-capture-device-camera-in-opencv

        #  print("frame2: ")
        #  print(frame2)

        #  print(self.webcamPlayer.video)
        frame = await self.track.recv()
        return frame


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform, webcamPlayer):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.webcamPlayer = webcamPlayer

    async def recv(self):

        #  ret, frame2 = vid.read()

        #  https://stackoverflow.com/questions/43665208/how-to-get-the-latest-frame-from-capture-device-camera-in-opencv

        #  print("frame2: ")
        #  print(frame2)

        #  print(self.webcamPlayer.video)
        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")

        frame2 = await self.webcamPlayer.video.recv()
        img2 = frame2.to_ndarray(format="bgr24")

        try:
            img = np.concatenate((img, img2), axis=1)
        except Exception as e:
            pass

        #  frame = await self.webcamPlayer.video.recv()
        #  img = frame.to_ndarray(format="bgr24")

        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


