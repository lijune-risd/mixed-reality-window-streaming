import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import time

import numpy as np

from av import VideoFrame
import cv2
from aiohttp import web

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay

# from overlay import replace_background
import mediapipe as mp
#  from MediaStreamTracks.CustomTracks import NoTransformTrack
#  from MediaStreamTracks.CustomTracks import VideoTransformTrack
#  from MediaStreamTracks.CustomTracks import GuestTransformTrack
#  from MediaStreamTracks.CustomTracks import WindowTransformTrack

ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")

#  pcs = [None, None, None]
#  pcs = set()
pcs = {}
curClient = None
relay = MediaRelay()
# initialize mediapipe
mp_selfie_segmentation = mp.solutions.selfie_segmentation
selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation()


def replace_background(fg, bg):
    bg_image = bg
    frame = fg

    # initialize mediapipe
    # mp_selfie_segmentation = mp.solutions.selfie_segmentation
    # selfie_segmentation = mp_selfie_segmentation.SelfieSegmentation()

    RGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # get the result
    results = selfie_segmentation.process(RGB)

    mask = results.segmentation_mask
    mask = cv2.GaussianBlur(mask, (33, 33), 0)

    # it returns true or false where the condition applies in the mask
    condition = np.stack(
        (mask,) * 3, axis=-1) > 0.6
    height, width = frame.shape[:2]
    # resize the background image to the same size of the original frame
    bg_image = cv2.resize(bg_image, (width, height))
    output_image = np.where(condition, frame, bg_image)
    return output_image


class TransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track, for both front, back, and guest
    """
    kind = "video"

    def __init__(self, track, transform, isGuest):
        super().__init__()  
        self.track = track
        self.transform = transform
        self.isGuest = isGuest

    async def recv(self):
        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")
        string = "guest"
        if self.isGuest:
            string = "windowFront"

        if string not in pcs:
            #  if not self.guestTrack:
            return frame

        n_track = pcs[string].getReceivers()[0].track
        n_frame = await n_track.recv()
        n_img = n_frame.to_ndarray(format="bgr24")

        frame = await self.track.recv()
        img = frame.to_ndarray(format="bgr24")

        try:
            img = replace_background(n_img, img)
            #  img = np.concatenate((img, guestImg), axis=1)
        except Exception as e:
            pass

        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame


async def windowoffer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # offerTypes: windowFront, windowBack, guest, offer, or dashboard
    offerType = params["offerType"]

    if offerType == "dashboard":
        print("length of pcs: ", len(pcs))
        pc = list(pcs)[0]
    else:
        pc = RTCPeerConnection()
        pc_id = "PeerConnection(%s)" % uuid.uuid4()
        if offerType != "offer":
            pcs[params["offerType"]] = pc
        else:
            pcs.add(pc)
        print("PCS: ")
        print(pcs)


    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "assets/demo-instruct.wav"))
    recorder = MediaBlackhole()

    # Open webcam on OS X for the offer case
    webcamPlayer = MediaPlayer('default:none', format='avfoundation', options={
        'framerate': '30',
        'video_size': '640x480'
    })

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            pc.addTrack(player.audio)
            recorder.addTrack(track)
        elif track.kind == "video":
            if offerType == "offer":
                pc.addTrack(
                    VideoTransformTrack(
                        relay.subscribe(track), transform=params["video_transform"], webcamPlayer=webcamPlayer)
                )
            elif offerType == "dashboard":
                pc.addTrack(
                    NoTransformTrack(
                        relay.subscribe(track), transform=params["video_transform"])
                )
            else:
                pc.addTrack(
                    TransformTrack(
                        track, transform=params["video_transform"], isGuest=(offerType == "guest"))
                )

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

### WEB FUNCTIONS #########################################################
async def windowpage(request):
    content = open(os.path.join(ROOT, "views/window.html"), "r").read()
    return web.Response(content_type="text/html", text=content)

async def windowjs(request):
    content = open(os.path.join(ROOT, "views/window.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


# -------- I don't think these 2 are necessary? I can't find any usages but I want to confirm that ----
async def windowBackpage(request):
    content = open(os.path.join(ROOT, "views/windowBack.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def windowBackjs(request):
    content = open(os.path.join(ROOT, "views/windowBack.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)
# ----------------------------------------------------------------------------------------------------

async def guestpage(request):
    content = open(os.path.join(ROOT, "views/guest.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def guestjs(request):
    content = open(os.path.join(ROOT, "views/guest.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

async def index(request):
    content = open(os.path.join(ROOT, "views/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "views/client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def dashboardpage(request):
    content = open(os.path.join(ROOT, "views/dashboard.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def dashboardjs(request):
    content = open(os.path.join(ROOT, "views/dashboard.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

###############################################################################

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


logging.basicConfig(level=logging.INFO)
ssl_context = None

app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_get("/", index)
app.router.add_get("/client.js", javascript)

app.router.add_get("/dashboard", dashboardpage)
app.router.add_get("/dashboard.js", dashboardjs)

app.router.add_get("/guest", guestpage)
app.router.add_get("/guest.js", guestjs)

app.router.add_get("/window", windowpage)
app.router.add_get("/window.js", windowjs)
app.router.add_post("/windowoffer", windowoffer)
