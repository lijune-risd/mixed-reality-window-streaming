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

import mediapipe as mp

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

window_video_track = None
guest_video_track = None

def replace_background(fg, bg):
    bg_image = bg
    frame = fg


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


class WindowTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.channel = None

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

        await self.channel._RTCDataChannel__transport._data_channel_flush()
        await self.channel._RTCDataChannel__transport._transmit()

        return new_frame

        #  frame = await self.track.recv()
        #  return frame


class WindowBackTransformTrack(MediaStreamTrack):
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




class GuestTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.channel = None

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

        await self.channel._RTCDataChannel__transport._data_channel_flush()
        await self.channel._RTCDataChannel__transport._transmit()

        return new_frame


async def windowpage(request):
    content = open(os.path.join(ROOT, "views/window.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def windowjs(request):
    content = open(os.path.join(ROOT, "views/window.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def windowoffer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs["windowFront"] = pc
    print("PCS: ")
    print(pcs)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "assets/demo-instruct.wav"))
    recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        global window_video_track
        window_video_track.channel = channel

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

        global window_video_track 
        window_video_track = WindowTransformTrack(track, transform=params["video_transform"])
        pc.addTrack(window_video_track)

        #  if track.kind == "audio":
        #      pc.addTrack(player.audio)
        #      recorder.addTrack(track)
        #  elif track.kind == "video":

        #      pc.addTrack(
        #          WindowTransformTrack(
        #              track, transform=params["video_transform"])
        #      )

            #  relay.subscribe(track), transform=params["video_transform"])
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


async def windowBackpage(request):
    content = open(os.path.join(ROOT, "views/windowBack.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def windowBackjs(request):
    content = open(os.path.join(ROOT, "views/windowBack.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def windowBackoffer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs["windowBack"] = pc
    print("PCS: ")
    print(pcs)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "assets/demo-instruct.wav"))
    recorder = MediaBlackhole()

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

            pc.addTrack(
                WindowBackTransformTrack(
                    track, transform=params["video_transform"])
            )

            #  relay.subscribe(track), transform=params["video_transform"])
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


async def guestpage(request):
    content = open(os.path.join(ROOT, "views/guest.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def guestjs(request):
    content = open(os.path.join(ROOT, "views/guest.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def guestoffer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    #  pcs.add(pc)
    #  pcs[0] = pc
    pcs["guest"] = pc
    print("PCS: ")
    print(pcs)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "assets/demo-instruct.wav"))
    recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")

        global guest_video_track
        guest_video_track.channel = channel

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

        global guest_video_track 
        guest_video_track = WindowTransformTrack(track, transform=params["video_transform"])
        pc.addTrack(guest_video_track)

        #  if track.kind == "audio":
        #      pc.addTrack(player.audio)
        #      recorder.addTrack(track)
        #  elif track.kind == "video":

        #      pc.addTrack(
        #          GuestTransformTrack(
        #              (track), transform=params["video_transform"])
        #      )
            #  relay.subscribe(track), transform=params["video_transform"])

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


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)
    curClient = pc
    print("PCS: ")
    print(pcs)

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
    recorder = MediaBlackhole()

    # Open webcam on OS X.
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

            pc.addTrack(
                VideoTransformTrack(
                    relay.subscribe(track), transform=params["video_transform"], webcamPlayer=webcamPlayer)
            )
            #  if args.record_to:
            #      recorder.addTrack(relay.subscribe(track))

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


async def dashboardOffer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    print("length of pcs: ", len(pcs))
    pc = list(pcs)[0]

    def log_info(msg, *args):
        logger.info(" " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    player = MediaPlayer(os.path.join(ROOT, "demo-instruct.wav"))
    recorder = MediaBlackhole()

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

            pc.addTrack(
                NoTransformTrack(
                    relay.subscribe(track), transform=params["video_transform"])
            )
            #  if args.record_to:
            #      recorder.addTrack(relay.subscribe(track))

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    #  await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


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
app.router.add_post("/offer", offer)

app.router.add_get("/dashboard", dashboardpage)
app.router.add_get("/dashboard.js", dashboardjs)
app.router.add_post("/dashboardOffer", dashboardOffer)

app.router.add_get("/guest", guestpage)
app.router.add_get("/guest.js", guestjs)
app.router.add_post("/guestoffer", guestoffer)

app.router.add_get("/window", windowpage)
app.router.add_get("/window.js", windowjs)
app.router.add_post("/windowoffer", windowoffer)
