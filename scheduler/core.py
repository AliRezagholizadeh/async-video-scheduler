import re

from scheduler.video import Video, VideoInAction
import asyncio
from typing import Dict
import datetime
import os
import logging
import ffmpeg
from pathlib import Path
from scheduler.video import Video, VideoInAction


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        # self.server_address = "127.0.0.1"
        self.server_address = "localhost"
        self.server_port = "1935"
        self.server_stream_protocol = "rtmp"


    async def set_run_schedule(self):
        time = self.program_schedule["program_schedule"]["start_time"]
        assert isinstance(time, datetime.time), f"time is not in datetime.time format, it is: {type(time)}"
        # video_file_path = "/Users/earthisgreen/Documents/Programming Space/ُTo publish in Bitbucket or Git hub/GitHub/Non_Profit_Organizations/Noor_Cultural_Center/async-video-scheduler/source/video/body1/1-body_rain.mp4"
        # video_file_path = Path("/Users/earthisgreen/Documents/Programming Space/ُTo publish in Bitbucket or Git hub/GitHub/Non_Profit_Organizations/Noor_Cultural_Center/async-video-scheduler/source/video/body1/02_somna_00_46.mp4")
        video_dir_path = Path("/Users/earthisgreen/Documents/Programming Space/ُTo publish in Bitbucket or Git hub/GitHub/Non_Profit_Organizations/Noor_Cultural_Center/async-video-scheduler/source/video/body1/")

        # path_ = video_file_path
        path_ = video_dir_path
        root_videoInAct = None
        if(path_.is_file()):  # single scheduled video
            # making video object of current video tuple
            video = Video(name="rain", path= str(path_))
            # making video in action object of current video obj
            root_videoInAct = VideoInAction(config= self.config, Video = video, PlayingDateTime= time)

        elif(path_.is_dir()): # multiple scheduled videos
            video_file_list = []
            for child_file in path_.iterdir():
                name = child_file.name
                format = child_file.suffix
                if(format not in self.config["Video_format"]):
                    continue

                # list names in with certain pattern: ex. 02_video_name
                m = re.findall(r"\b\d+-*[\w-]*", name)
                if(m): # match
                    video_file_list.append((child_file, m[0], format))
            # sort video based on the initial number
            video_file_list = sorted(video_file_list, key=lambda x: int(re.findall(r"^\d+", x[1])[0]))

            # create Video and nested VideoInAction objects
            video_inAct_obj = None
            for video_indx in range(len(video_file_list)):
                # making video object of current video tuple
                v_tup = video_file_list[video_indx]
                # making video in action object of current video obj
                video_obj = Video(name=v_tup[1], path= str(v_tup[0]))

                prev_videoInAct = video_inAct_obj

                if (video_inAct_obj): # after the first iteration
                    v_inAct_obj = VideoInAction(Video=video_obj, PreviousVideo=prev_videoInAct, config=self.config)
                    video_inAct_obj.NextVideo = v_inAct_obj
                else: # at first iteration
                    v_inAct_obj = VideoInAction(Video=video_obj, PreviousVideo=prev_videoInAct, config=self.config, PlayingDateTime= time)
                    root_videoInAct = v_inAct_obj

                video_inAct_obj = v_inAct_obj


        else: # not recognized
            raise ValueError("Video file path is not reffering to a file or a dir.")

        print(f"From Core (program_pipeline) \nroot_videoInAct: {root_videoInAct}")
        task = asyncio.create_task(root_videoInAct.on_time_stream())
        print(f"trigger_timely_video called to be ran at {time} for {str(path_)}")
        await task

    # async def trigger_timely_video(self, scheduled_time: datetime.time, video_file_path:str):
    #     """
    #     Stands between the server and the local resources. It is set based on the scheduled time and video assigned.
    #     If time arrive, it will out the right timeslot of the video to the local RTMP server ran by the server method.
    #
    #     """
    #     while True:
    #         # time might needs to be improved to capture the streaming delays..
    #         if(not self.server_available_bool):
    #             print("waiting till the local server be set ..")
    #             await asyncio.sleep(0.5)
    #         else:
    #             if(datetime.datetime.now().time() >= scheduled_time):
    #                 #TODO: play the right timeslot of the video
    #                 try:
    #                     # out, err = ffmpeg.input(video_file_path, re=None).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run()
    #                     process = ffmpeg.input(video_file_path).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
    #                     # process = ffmpeg.input(video_file_path, ss= "00:00:40").output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
    #                     # process = ffmpeg.input(video_file_path, re=None).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv').run_async(pipe_stdout=True, pipe_stderr=True)
    #                      # "ffmpeg -i my_test_file.flv -c:v copy -c:a copy -f flv "rtmp://localhost:1935/live/stream
    #                     print(f"trigger_timely_video: video ({video_file_path}) streamed to the server ..")
    #                     process.wait()
    #                     # print(f"trigger_timely_video: Error: {err},\n Out:{out}")
    #                 except ffmpeg.Error as e:
    #                     print(f"trigger_timely_video: An error occurred in loading video file to the server: {e}")
    #
    #                 print("wating on the stream.")
    #                 await asyncio.sleep(60)
    #                 break
    #
    #             else:
    #                 print(f"now: {datetime.datetime.now().time()}, scheduled_time: {scheduled_time}")
    #
    #                 await asyncio.sleep(0.5)
    #
    # async def trigger_timely_videos(self, scheduled_time: datetime.time, video_file_path: str):
    #     pass







class ProcessAgent:
    processes = {}
    def __init__(self):
        pass

    @classmethod
    def put_process(cls, process_id: str, process):
        assert isinstance(process, dict), "process is not in dict type."
        cls.processes.append(process)

