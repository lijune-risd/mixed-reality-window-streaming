
from av import VideoFrame
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
import numpy as np

class WindowTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform

    async def recv(self):

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")

        if "guest" not in pcs: 
        #  if not self.guestTrack: 
            return frame

        guestTrack = pcs["guest"].getReceivers()[0].track

        guestFrame = await guestTrack.recv()
        guestImg = guestFrame.to_ndarray(format="bgr24")

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")

        try:
            img = replace_background(guestImg, img)
            #  img = np.concatenate((img, guestImg), axis=1)
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

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform

    async def recv(self):

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")

        if "windowFront" not in pcs: 
            return frame

        windowFrontTrack = pcs["windowFront"].getReceivers()[0].track
        #  img = frame.to_ndarray(format="bgr24")
        # strip background from img

        windowFrontFrame = await windowFrontTrack.recv()
        windowFrontImg = windowFrontFrame.to_ndarray(format="bgr24")

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")


        #  frame = await self.track.recv()


        #  img = np.concatenate((img, img), axis=1)
        try:
            #  img = np.concatenate((img, windowFrontImg), axis=1)
            img = replace_background(img, windowFrontImg)
        except Exception as e:
            pass


        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
