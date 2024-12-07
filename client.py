import argparse
import asyncio
import json
import logging
import os
import ssl
import uuid
import socket
import cv2
from aiohttp import web
from av import VideoFrame

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from copy import copy
import time
import sys
from collections import deque
import traceback
import inspect
import numpy as np
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import uuid
from aiortc.stats import RTCStatsReport 

id=uuid.uuid4()
# Use a service account.
cred = credentials.Certificate('service.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()



ROOT = os.path.dirname(__file__)

logger = logging.getLogger("pc")
pcs = set()

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)

portnumber = None
print("Your Computer IP Address is:" + IPAddr)
clients={}
pc_id_map={}
relay=MediaRelay()
relay_modified=MediaRelay()

# class RoundRobin:
#     def __init__(self,id,):


class MinRTT:
    def __init__(self,alpha=0.125):
        self.pcs={}
        self.count=0
        self.threshold=5
        self.alpha=alpha

    def add_pc(self,gid):
        print("ADDING PC = ",gid)
        self.pcs[gid]=1e9       
    async def log_stats(self,interval=5.0):
        self.count+=1
        rtt=1e9
        i=1
        while i<=len(self.pcs):
            # pc  = pc_id_map[i]
            pc = pc_id_map[i]
            id = i
            print("PC = ",pc)
            print("Connection State = ",pc.connectionState) 
            if pc.connectionState!="closed":
                
                print("----------- HERE -----------------")
                stats = await pc.getStats()
                print("-------------------------- SURI ------------------")
                for report in stats.values():

                    # print(report)

                    # print(report)
                    print("REPORT = ",report)
                    if report.type == "remote-inbound-rtp" and report.kind == "video":
                        print("PC = ",pc)
                        print("id = ",id)
                        print("RTT = ",report.roundTripTime)
                        if report.roundTripTime==None:
                            rtt=0
                        else:
                            rtt=report.roundTripTime
                
                        print("pcs = ",self.pcs)
                        print(len(self.pcs.keys()))
                        if len(self.pcs.keys())==0:
                            self.pcs[id]=rtt
                        else:
                            print("HERE ")
                            self.pcs[id] = self.alpha *rtt + (1 - self.alpha) * self.pcs[id]   
            i+=1     
        await asyncio.sleep(interval)
        await self.log_stats()

    
    def get_optimal_pc(self):
        minRTT=1e9
        optimal_pc=None
        print("PCS = ",self.pcs)
        if len(self.pcs.keys())==0:
            return None
        for pc in self.pcs.keys():
            print(self.pcs)
            if self.pcs[pc]<minRTT:
                minRTT=self.pcs[pc]
                optimal_pc=pc
        if optimal_pc==None:
            return None
        return optimal_pc

MinRTT_scheduler=MinRTT()  
#    print("PC VALLLLL = ",pc)


class VideoTransformTrackchild(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    kind = "video"
    def __init__(self, track,id):
        super().__init__()  # don't forget this!
        self.parent_relay=track
        self.rid=id
    

    async def recv(self):
        frame = await self.parent_relay.recv(self.rid)
        return frame
       
class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    kind = "video"
    def __init__(self, track, transform,rid):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.frameidx=0
        self.rid=rid

    async def recv(self,id=None):
        # if MinRTT_scheduler.count<=MinRTT_scheduler.threshold:
        frame = await self.track.recv()

        if id!=None:
            print("id",id," frameidx",self.frameidx)

            optimal_id = MinRTT_scheduler.get_optimal_pc()
            print("OPTIMAL ID = ",optimal_id)   

            if optimal_id!=None:
                return self.process_frame(frame)   
            else:
                return self.process_frame(frame,transform="empty") 
        else:
            return self.process_frame(frame)   
    
    def process_frame(self,frame,transform=None):

        if transform == "cartoon":
            img = frame.to_ndarray(format="bgr24")
            # prepare color
            img_color = cv2.pyrDown(cv2.pyrDown(img))
            for _ in range(6):
                img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
            img_color = cv2.pyrUp(cv2.pyrUp(img_color))
            # prepare edges
            img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img_edges = cv2.adaptiveThreshold(cv2.medianBlur(img_edges, 7),255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,9,2,)
            img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)
            # combine color and edges
            img = cv2.bitwise_and(img_color, img_edges)
            # rebuild a VideoFrame, preserving timing information
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        
        elif transform == "edges":
            # perform edge detection
            img = frame.to_ndarray(format="bgr24")
            img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)
            # rebuild a VideoFrame, preserving timing information
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        
        elif transform == "rotate":
            # rotate image
            img = frame.to_ndarray(format="bgr24")
            rows, cols, _ = img.shape
            M = cv2.getRotationMatrix2D((cols / 2, rows / 2), frame.time * 45, 1)
            img = cv2.warpAffine(img, M, (cols, rows))
            # rebuild a VideoFrame, preserving timing information
            new_frame = VideoFrame.from_ndarray(img, format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        
        elif transform == "empty":
            img = frame.to_ndarray(format="bgr24")
            img.fill(np.uint8(0))
            new_frame = VideoFrame.from_ndarray(img,format="bgr24")
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        
        else:
            return frame


async def index(request):
    global IPAddr
    content = open(os.path.join(ROOT, "client.html"), "r").read()
    content = content.replace("{{IPAddress}}", IPAddr+":"+str(portnumber))
    content = content.replace("{{id}}",str(id))
    return web.Response(content_type="text/html", text=content)

async def javascript(request):
    content = open(os.path.join(ROOT, "client3.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

# async def javascript2(request):
    # content = open(os.path.join(ROOT, "create_elements.js"), "r").read()
    # print(content)
    # return web.Response(content_type="application/javascript", text=content)

get_req_response=None
get_req_response2=None
pcs = set() # dictionary to store sdp,offer with pc
i=0
d={}
relay_id=0
child_relays=set()
gid=0

async def offer(request):
    global get_req_response,i,d,get_req_response2,relay_modified,gid
    params = await request.json()
 
    if params["livestream"]==True:#send stream from server to client
        print("HELLO WORLD FROM LS")
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        # Setup  multiple RTC sessions
        pc = RTCPeerConnection()
        pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                pcs.discard(pc)
        
        if get_req_response!=None:
            pc.addTrack(VideoTransformTrackchild(
                get_req_response,id=gid))
            pc_id_map[gid]=pc
            MinRTT_scheduler.add_pc(gid)
            gid+=1
            # pc.addTrack(get_req_response)

        print("offer from client")
        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # Start logging of stats
        # asyncio.create_task(log_stats(pc)) 
        # gid+=1
      

        db.collection("calls").document(params['roomid']).set({str(params['clientid']):{"answer":{'sdp':pc.localDescription.sdp,'type':pc.localDescription.type}}},merge=True)
        
        # await firestore.collection("calls").doc(params['callid']).

        response = web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )
        # Allow all origins here
        response.headers["Access-Control-Allow-Origin"] = "*"
        # Allow all methods
        response.headers["Access-Control-Allow-Methods"] = "*"
        # Allow all headers
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    
    else:
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
    
        pc_id = "PeerConnection(%s)" % uuid.uuid4()

        def log_info(msg, *args):
            logger.info(pc_id + " " + msg, *args)

        log_info("Created for %s", request.remote)

        # prepare local media
        if args.record_to:
            recorder = MediaRecorder(args.record_to)
        else:
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
            global get_req_response,calls
            log_info("Track %s received", track.kind)
            if track.kind == "audio":
                pass
                # # pc.addTrack(player.audio)
                # # recorder.addTrack(track)

            elif track.kind == "video":
                video=VideoTransformTrack(
                    relay.subscribe(track), transform=params["video_transform"],rid=0
                )
                
                get_req_response=VideoTransformTrack(
                    relay_modified.subscribe(track), transform=params["video_transform"],rid=1
                )

                pc.addTrack(video)
                if args.record_to:
                    recorder.addTrack(relay.subscribe(track))
                    
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

        # Start logging of stats
        asyncio.create_task(MinRTT_scheduler.log_stats())

        # asyncio.create_task(log_stats(pc))  
        

        print(get_req_response)
        response =  web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )
        # Allow all origins here
        response.headers["Access-Control-Allow-Origin"] = "*"
        # Allow all methods
        response.headers["Access-Control-Allow-Methods"] = "*"
        # Allow all headers
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

async def handle_options(request):
    response = web.Response()
    # Allow all origins here
    response.headers["Access-Control-Allow-Origin"] = "*"
    # Allow all methods
    response.headers["Access-Control-Allow-Methods"] = "*"
    # Allow all headers
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

async def getuuid(request):
    params=await request.json()
    ids=[]
    for i in range(int(params['num_connections'])):
        id=uuid.uuid4()
        ids.append(str(id))
    
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"uuids": ids}
        ),
    )

if __name__ == "__main__":
   
    parser = argparse.ArgumentParser(
        description="WebRTC audio / video / data-channels demo"
    )
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--record-to", help="Write received media to a file."),
    parser.add_argument("--verbose", "-v",default=False,action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None
    portnumber = args.port
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    # Add arguments to the api endpoint

    app.router.add_get("/client", index)
    # app.router.add_get("/create_elements.js",javascript2)
    app.router.add_get("/client3.js", javascript)
    app.router.add_post("/offer", offer)
    app.router.add_options("/offer",handle_options)
    app.router.add_post("/getuuid",getuuid)
    web.run_app(
        app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    )
 