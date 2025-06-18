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
from scheduler.utils import ReqDateTimeFormatProperty, ValidDateTimeFormat, \
    CurrentDTimeProperty, CLOCKProperty, ReqField, TIME_FORMATS

from typing import List

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# import functools
# def setclock_wrapper(func):
#
#     @functools.wraps(func)
#     def wrapped(cls, *args, **kwargs):
#         cls.CLOCK = CLOCKProperty()
#         func(*args, **kwargs)
#
#     return wrapped

class SetClockVar:
    def __init__(self, func):
        self.func = func

    def wrap(cls, original_method):
        # This is the actual wrapper function that will be returned
        def wrapper(instance, *args, **kwargs):
            print("cls in wrap: ", cls.__name__)

            cls.CLOCK = CLOCKProperty()
            print(f"Calling {original_method.__name__}...")
            original_method(instance, *args, **kwargs)
            print(f"{original_method.__name__} finished.")


        return wrapper


class Program_core:
    _instance = None
    Start_DTime = ReqDateTimeFormatProperty(ValidDateTimeFormat)
    Current_DTime = CurrentDTimeProperty()
    # Passed_DTime = None
    CLOCK = None
    Name = ReqField(str)

    def __init__(self, start_dtime: str, root_program_path: str = None, name:str = None):
        self.root_program_path = root_program_path
        self.Start_DTime = start_dtime
        self.base_datetime = datetime.datetime(year=self.Start_DTime.year, month= self.Start_DTime.month, day= self.Start_DTime.day)
        self.start_program_siganl = asyncio.Event()
        self.program_queue = asyncio.Queue()
        self.end_program_siganl = asyncio.Event()
        self.Name = name
        self.pulse_event = None
        self.ordered_schedule: List = None   # [(dTime, video_in_action), ..]

    def __new__(cls, *args, **kwargs):
        # print("program_core __new__")
        if not cls._instance:
            cls.CLOCK = CLOCKProperty()
            cls._instance = super().__new__(cls)
        return cls._instance

    # @SetClockVar(Program_core).wrap
    async def __aenter__(self, *args, **kwargs):
        # print("Enter with")
        self.clock_task = asyncio.create_task(self.CLOCK.timer())
        self.pulse_event = self.CLOCK.get_event()
        # print("pulse_event: ", self.pulse_event)
        # print("Program create _ before yield")
        # print("Program create _ before yield")


        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("program to be exited")
        await self.clock_task
        print("program exited")

    @property
    def Passed_DTime(self):
        current_dtime, _ = self.Current_DTime
        return current_dtime - self.Start_DTime

    async def Clock_Updater(self):
        # print("Clock_Updater ..")
        while(not self.end_program_siganl.is_set()):
            # print("... waiting pulse_event be set ..")
            await self.pulse_event.wait()
            # print(" ... To Consume the pulse..")
            try:
                # Timer
                if(self.Passed_DTime.days < 0):
                    # print(f"Count down to start the program: {self.Passed_DTime}")
                    passed = (self.base_datetime - self.Passed_DTime).time().strftime(TIME_FORMATS[1])

                    print(f"\rCount down to start the program: {passed}", end= "")
                else:
                    passed = (self.base_datetime + self.Passed_DTime).time().strftime(TIME_FORMATS[1])
                    print(f"\rProgram Timer: {passed}", end= "")

                # Schedule handler : Select the earlier video and specify the point it should be streamed.
                if(self.ordered_schedule and self.ordered_schedule[-1](0) <= self.Current_DTime[0]): # check if the time to show the earliest content just arrived..
                    content_dTime = self.ordered_schedule[-1](0)
                    fromTime = (self.base_datetime + (self.Current_DTime[0] - content_dTime)).time().strftime(TIME_FORMATS[1])

                    self.stream(self.ordered_schedule.pop(), fromTime)
            except Exception as e:
                print(f"ERROR: {e}")
            self.pulse_event.clear()


            # while(not self.pulse_event.is_set()):
            #     print("... waiting pulse_event be set ..")
            #     await asyncio.sleep(1)
            #     print("clock_updater: after sleep")
            #     # print(f"{self}", end="")
            # # print(f"{self}", end="")
            # if(self.pulse_event.is_set()):
            #     print("To Consume the pulse..")
            #     self.pulse_event.clear()

    def setBySchedule(self, schedule):
        pass

    def scheduler(self):
        """Processes the list of contents and pass it to the asyncio.Queue video by video to let run-function drain it.
        Decides which video and from what point should be streamed."""
        pass

    def stream(self, Video: VideoInAction, fromTime: str):
        """"""
        pass

    async def run(self):
        # if(not self.start_program_siganl.is_set()):
        #     print("Wait running till the program is set by the schedule.")
        #     await self.start_program_siganl.wait()

        # start program's clock
        prog_clk_updater = asyncio.create_task(self.Clock_Updater())

        # video_dict = await self.program_queue.get()
        # build video in action object




        await prog_clk_updater
        print("Program Ended.")

    def __str__(self):
        # passed time from the beginning of the program.
        passed = (self.base_datetime + self.Passed_DTime).time().strftime(TIME_FORMATS[1])
        return f"Program Name: {self.Name} \n" \
               f"Start time: {self.Start_DTime} \n" \
               f"Current time: {self.Current_DTime.time()} \n" \
               f"Passed time: {passed}"

    def __repr__(self):
        passed = (self.base_datetime + self.Passed_DTime).time().strftime(TIME_FORMATS[1])
        return f"Passed time: {passed}"





class Program:
    def __aenter__(self):
        return self
    @classmethod
    async def create(self, *args, **kwargs):
        # self = super().__new__(cls, *args, **kwargs)
        print("Program create..")
        Program_core.CLOCK = CLOCKProperty()

        async with Program_core(*args, **kwargs) as program:
            print("Program create: to return program object")
            return program
            print("Program create: returned")


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
        video_dir_path = Path("/source/video/Daily_Contents/body1/")

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

