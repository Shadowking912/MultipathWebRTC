from aiortc.contrib.media import MediaStreamTrack, MediaStreamError,RelayStreamTrack,logger,RelayStreamTrack
from typing import Dict, Optional, Set, Union
import asyncio
import inspect
import traceback


class MediaRelay_modified:
    """
    A media source that relays one or more tracks to multiple consumers.

    This is especially useful for live tracks such as webcams or media received
    over the network.
    """

    def __init__(self,id) -> None:
        self.__proxies: Dict[MediaStreamTrack, Set[RelayStreamTrack]] = {}
        self.__tasks: Dict[MediaStreamTrack, asyncio.Future[None]] = {}
        self.id=id

    def subscribe(
        self, track: MediaStreamTrack, buffered: bool = False) -> MediaStreamTrack:
        """
        Create a proxy around the given `track` for a new consumer.

        :param track: Source :class:`MediaStreamTrack` which is relayed.
        :param buffered: Whether there need a buffer between the source track and
            relayed track.

        :rtype: :class: MediaStreamTrack
        """
        proxy = RelayStreamTrack(self, track, buffered)
        self.__log_debug("Create proxy %s for source %s relayid:%s", id(proxy), id(track),self.id)
        if track not in self.__proxies:
            self.__proxies[track] = set()
        return proxy

    def _start(self, proxy: RelayStreamTrack) -> None:
        track = proxy._source
        if track is not None and track in self.__proxies:
            # register proxy
            if proxy not in self.__proxies[track]:
                self.__log_debug("Start proxy %s relayid:%s for source %s", id(proxy),self.id,id(track))
                self.__proxies[track].add(proxy)

            # start worker
            if track not in self.__tasks:
                self.__tasks[track] = asyncio.ensure_future(self.__run_track(track))

    def _stop(self, proxy: RelayStreamTrack) -> None:
        track = proxy._source
        if track is not None and track in self.__proxies:
            # unregister proxy
            self.__log_debug("Stop proxy %s", id(proxy))
            self.__proxies[track].discard(proxy)

    def __log_debug(self, msg: str, *args) -> None:
        logger.debug(f"MediaRelay(%s) {msg}", id(self), *args)

    async def __run_track(self, track: MediaStreamTrack) -> None:
        self.__log_debug("Start reading source %s" % id(track))

        while True:
            try:
                frame = await track.recv(self.id)
            except MediaStreamError:
                frame = None
            for proxy in self.__proxies[track]:
                
                if proxy._buffered:
                    proxy._queue.put_nowait(frame)
                else:
                    proxy._frame = frame
                    proxy._new_frame_event.set()
            if frame is None:
                break

        self.__log_debug("Stop reading source %s", id(track))
        del self.__proxies[track]
        del self.__tasks[track]


