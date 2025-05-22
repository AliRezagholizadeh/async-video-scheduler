import asyncio
from typing import Dict
import datetime
import os
import logging


from pyrtmp import StreamClosedException
from pyrtmp.flv import FLVFileWriter, FLVMediaType
from pyrtmp.session_manager import SessionManager
from pyrtmp.rtmp import SimpleRTMPController, RTMPProtocol, SimpleRTMPServer
from pyrtmp.rtmp import

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RTMP2FLVController(SimpleRTMPController):

    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        super().__init__()

    async def on_ns_publish(self, session, message) -> None:
        publishing_name = message.publishing_name
        file_path = os.path.join(self.output_directory, f"{publishing_name}.flv")
        session.state = FLVFileWriter(output=file_path)
        await super().on_ns_publish(session, message)

    async def on_metadata(self, session, message) -> None:
        session.state.write(0, message.to_raw_meta(), FLVMediaType.OBJECT)
        await super().on_metadata(session, message)

    async def on_video_message(self, session, message) -> None:
        session.state.write(message.timestamp, message.payload, FLVMediaType.VIDEO)
        await super().on_video_message(session, message)

    async def on_audio_message(self, session, message) -> None:
        session.state.write(message.timestamp, message.payload, FLVMediaType.AUDIO)
        await super().on_audio_message(session, message)

    async def on_stream_closed(self, session: SessionManager, exception: StreamClosedException) -> None:
        session.state.close()
        await super().on_stream_closed(session, exception)



class SimpleServer(SimpleRTMPServer):

    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        super().__init__()

    async def create(self, host: str, port: int):
        loop = asyncio.get_event_loop()
        self.server = await loop.create_server(
            lambda: RTMPProtocol(controller=RTMP2FLVController(self.output_directory)),
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
        self.server_port = "2025"
        self.server_stream_protocol = "rtmp"

    def server(self):
        """
        launch a RTMP serve to listen on coming stream and will emmit it over predefined options, like:
        - playback

        """


    async def trigger_timely_video(self, scheduled_time: datetime.time, video_dir:str):
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
                    pass
                else:
                    await asyncio.sleep(0.5)




