
from av import VideoFrame
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

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


