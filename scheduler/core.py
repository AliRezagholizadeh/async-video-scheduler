import asyncio
from typing import Dict
import datetime
import os
import logging
import ffmpeg
from pathlib import Path
from pyrtmp import StreamClosedException
from pyrtmp.flv import FLVFileWriter, FLVMediaType
from pyrtmp.session_manager import SessionManager
from pyrtmp.rtmp import SimpleRTMPController, RTMPProtocol, SimpleRTMPServer
# from pyrtmp.rtmp import

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RTMPontroller(SimpleRTMPController):

    def __init__(self):
        super().__init__()

    async def on_ns_publish(self, session, message) -> None:
        publishing_name = message.publishing_name
        print(f"on publish. publishing_name: {publishing_name}")
        await super().on_ns_publish(session, message)

    async def on_metadata(self, session, message) -> None:
        session.state.write(0, message.to_raw_meta(), FLVMediaType.OBJECT)
        print(f"on metadata: {message.to_raw_meta()}")
        await super().on_metadata(session, message)

    async def on_video_message(self, session, message) -> None:
        session.state.write(message.timestamp, message.payload, FLVMediaType.VIDEO)
        print(f"on_video_message: {message.payload()}")

        await super().on_video_message(session, message)

    async def on_audio_message(self, session, message) -> None:
        session.state.write(message.timestamp, message.payload, FLVMediaType.AUDIO)
        print(f"on_audio_message: {message.payload()}")

        await super().on_audio_message(session, message)

    async def on_stream_closed(self, session: SessionManager, exception: StreamClosedException) -> None:
        session.state.close()
        print(f"on_stream_closed: {session.state}")

        await super().on_stream_closed(session, exception)



class SimpleServer(SimpleRTMPServer):

    def __init__(self):
        super().__init__()

    async def create(self, host: str, port: int):
        loop = asyncio.get_event_loop()
        self.server = await loop.create_server(
            lambda: RTMPProtocol(controller=RTMPontroller()),
            host=host,
            port=port,
        )


class program_pipeline:
    """
    This pipeline aims at building RTMP streaming to let the user bind it to a program schedule and actively follow it.
    It means the pipeliine wait till start of the program. Then, start playing the streaming from the determined source.
    If a problem happens during a runtime (for local machine or the remote receiver), this pipeline will reconnect from
    the video timeslot it supposed to play in the case it ran properly.

    This pipeline aims at providing the capability of adding live text (label or rolling text) and layout to the pipeline.

    The technologies used are:
    - FFMPEG
    - CV2
    -
    """
    def __init__(self, config: Dict, program_schedule: Dict):
        self.config = config
        self.program_schedule = program_schedule
        self.server_available_bool = False
        self.server_address = "127.0.0.1"
        self.server_port = "1935"
        self.server_stream_protocol = "rtmp"

    async def run_server(self):
        """
        launch a RTMP serve to listen on coming stream and will emmit it over predefined options, like:
        - playback

        """

        server = SimpleServer()
        await server.create(host=self.server_address, port=self.server_port)
        await server.start()
        self.server_available_bool = True

        await server.wait_closed()
        print("server closed ..")

    async def set_run_schedule(self):
        time = self.program_schedule["program_schedule"]["start_time"]
        assert isinstance(time, datetime.time), f"time is not in datetime.time format, it is: {type(time)}"
        video_file_path = "/Users/earthisgreen/Documents/Programming Space/ُTo publish in Bitbucket or Git hub/GitHub/Non_Profit_Organizations/Noor_Cultural_Center/async-video-scheduler/source/video/body1/1-body_rain.mp4"
        task = asyncio.create_task(self.trigger_timely_video(time, video_file_path))
        print(f"trigger_timely_video called to be ran at {time} for {Path(video_file_path).parents[-3:]}")
        await task

    async def trigger_timely_video(self, scheduled_time: datetime.time, video_file_path:str):
        """
        Stands between the server and the local resources. It is set based on the scheduled time and video assigned.
        If time arrive, it will out the right timeslot of the video to the local RTMP server ran by the server method.

        """
        while True:
            # time might needs to be improved to capture the streaming delays..
            if(not self.server_available_bool):
                print("waiting till the local server be set ..")
                await asyncio.sleep(0.5)
            else:
                if(datetime.datetime.now().time() >= scheduled_time):
                    #TODO: play the right timeslot of the video
                    try:
                        # out, err = ffmpeg.input(video_file_path).output(f"rtmp://{self.server_address}:{self.server_port}/test/sample", vcodec = "copy", acodec= "copy").run()
                        process = ffmpeg.input(video_file_path, ss= "00:00:40").output(f"rtmp://{self.server_address}:{self.server_port}/", format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
                         # "ffmpeg -i my_test_file.flv -c:v copy -c:a copy -f flv "
                        print(f"trigger_timely_video: video ({video_file_path}) streamed to the server ..")
                        process.wait()
                        # print(f"trigger_timely_video: Error: {err},\n Out:{out}")
                    except ffmpeg.Error as e:
                        print(f"trigger_timely_video: An error occurred in loading video file to the server: {e}")
                    
                    break
                else:
                    print(f"now: {datetime.datetime.now().time()}, scheduled_time: {scheduled_time}")

                    await asyncio.sleep(0.5)




