from typing import List

from scheduler.utils import ReqPATH, ReqField, DateTimeFormatProperty, ValidTimeFormat, ValidDateTimeFormat, Either
from scheduler.utils import PlayingDateTimeProperty
from scheduler.streaming_utils import adjust_volume
from pathlib import Path
# from datetime import datetime
import datetime
import asyncio
import cv2
from moviepy import VideoFileClip
from pydub import AudioSegment

from enum import Enum
import tempfile
import os



class VideoStatus(Enum):
    NOTPLAYED = "Notplayed"
    COMPLAYED = "Played"
    RESUMED = "Resumed"
    ERROR = "Error"  # Error occurred during playing



class VideoProperty:
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value):
        if not isinstance(value, Video):
            raise ValueError(f'The {self.property_name} must be a Video')
        if(not value):
            raise ValueError(f'The {self.property_name} cannot be empty')

        instance.__dict__[self.property_name] = value

class VideoInActionProperty:
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value):
        if not isinstance(value, VideoInAction):
            raise ValueError(f'The {self.property_name} must be a VideoInAction')
        if(not value):
            raise ValueError(f'The {self.property_name} cannot be empty')

        instance.__dict__[self.property_name] = value






class Video:
    # Length = ReqDateTimeFormatProperty(ValidTimeFormat)
    PATH = ReqPATH()
    Name = ReqField(str)
    ToSound_dBFS = -14
    def __init__(self, name: str, path: str):
        # video properties
        self.PATH = path
        self.Name = name
        self._Resolution = None
        self._Length = None
        self._SoundStrength = None
        self._FPS = None
        self.changelog = ""


        self.adjust_video_audio_dB()
        print("passed adjust_video_audio_dB")
        self.get_videoInfo()
        print("passed get_videoInfo")

        print(self)

    # @property
    # def Name(self):
    #     return self._Name
    # @Name.setter
    # def Name(self, value):
    #     assert isinstance(value, str), f"Name should be in str format, but {type(value)} entered."
    #     if(self._Name):
    #         print(f"An attempt made to rename this video (i.e. {self._Name}) to {value}.")
    #     self._Name = value

    # @property
    # def Category(self):
    #     return
    @property
    def FPS(self):
        return self._FPS

    @property
    def Length(self):
        if(not self._Length):
            raise ValueError("Video length is not recognized.")
        return self._Length
    @property
    def Resolution(self):
        return self._Resolution

    @property
    def SoundStrength(self):
        return self._SoundStrength

    @classmethod
    def set_dBFS(cls, value):
        # ensure the value is below -1
        if(value > -1):
            cls.ToSound_dBFS = -1
        else:
            cls.ToSound_dBFS = value

    def __str__(self):
        return f"{('-')*20} \n" \
               f"{self.Name} Video Info:" \
               f" ----> Name: {self.Name}"\
               f" ----> Length: {self.Length}"\
               f" ----> Resolution: {self.Resolution}"\
               f" ----> Sound Strength: .... "\
               f" ----> PATH: {self.PATH}" \
               f" ----> changelog: {self.changelog}" \
               f"{('-') * 20} \n"


    # def set_properties(self, Name = None, Length = None, Resolution = None, VoiceStrength = None, PATH = None):
    #     assert PATH != None, "Path of the video is not determined."
    #     self.Name = Name
    #     self.Length = Length
    #     self.Resolution = Resolution
    #     self.VoiceStrength = VoiceStrength
    #     self.PATH = PATH


    def get_videoInfo(self):

        video = cv2.VideoCapture(self.PATH)

        self._Length = video.get(cv2.CAP_PROP_POS_MSEC)
        self._FPS = video.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._Resolution = f"{height}x{width}"



    # def adjust_video_audio_dB(self):
    #     # Google AI-generated function:
    #     # https://www.google.com/search?q=Is+there+any+way+to+adjust+sound+db+for+several+videos+in+python%3F&sca_esv=3f2684b5ae9554a2&rlz=1C5CHFA_enCA1000CA1000&sxsrf=AE3TifOFtlcJnjJ2wYNrp1OlNLNrpt5uzg%3A1748463084869&ei=7G03aOXjNNDV5NoP7LTOuQE&ved=0ahUKEwjlic7I_MaNAxXQKlkFHWyaMxcQ4dUDCBE&uact=5&oq=Is+there+any+way+to+adjust+sound+db+for+several+videos+in+python%3F&gs_lp=Egxnd3Mtd2l6LXNlcnAiQUlzIHRoZXJlIGFueSB3YXkgdG8gYWRqdXN0IHNvdW5kIGRiIGZvciBzZXZlcmFsIHZpZGVvcyBpbiBweXRob24_SIVIUNgKWK5GcAJ4AZABAJgBygGgAagIqgEFNy4zLjG4AQPIAQD4AQGYAgegApYFwgIKEAAYsAMY1gQYR8ICBRAAGO8FwgIIEAAYgAQYogTCAggQABiiBBiJBZgDAIgGAZAGCJIHBTMuMy4xoAe9HbIHBTEuMy4xuAeLBcIHBTAuMS42yAca&sclient=gws-wiz-serp
    #     #
    #
    #
    #     # 1. Extract Audio
    #     # clip = VideoFileClip(video_path)
    #     clip = VideoFileClip(self.PATH)
    #     audio = clip.audio
    #     clip.close()
    #
    #     if(audio is not None):
    #         # write the audio in a temporary .wav file
    #         temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    #         # audio.write_audiofile(temp_audio_file.name)
    #         print(audio)
    #         # audio.write_audiofile("audio.wav")
    #         audio.write_audiofile("audio.wav")
    #         # 2. Load into Pydub
    #         # audio_seg = AudioSegment.from_file(temp_audio_file.name)
    #         audio_seg = AudioSegment.from_file("audio.wav")
    #
    #         # 3. Adjust dB
    #         # Get the current dBFS (decibels Full Scale)
    #         current_dBFS = audio_seg.dBFS
    #         self.SoundStrength = current_dBFS
    #
    #         if(current_dBFS > -1):
    #             # Calculate the gain needed to reach the new dBFS
    #             gain_needed = self.ToSound_dBFS - current_dBFS
    #
    #             # Apply the gain
    #             modified_audio = audio_seg.apply_gain(gain_needed)
    #
    #             self.changelog += f"The base sound strength of {current_dBFS} is adjusted to {modified_audio.dBFS}.\n"
    #             # 4. Re-attach Audio
    #             # Replace the audio track with the modified audio (e.g., replace audio with 'modified_audio')
    #             new_clip = VideoFileClip(self.PATH)
    #             new_clip.audio = modified_audio
    #             self.SoundStrength = modified_audio.dBFS
    #             new_clip.write_videofile(self.PATH)
    #             new_clip.close()
    #
    #         os.unlink(temp_audio_file.name)
    #     else: # clip is silent
    #         self.changelog += f"Probable Warning: Clip is siltent.\n"


    def adjust_video_audio_dB(self):
        self.changelog += adjust_volume(self.PATH, self.ToSound_dBFS)



class VideoInAction:
    RTMPServerAddress = None

    Video = VideoProperty()
    PreviousVideo = VideoInActionProperty()
    NextVideo = VideoInActionProperty()

    # StartedTime = DateTimeFormatProperty(ValidTimeFormat)
    # EndTime = DateTimeFormatProperty(ValidTimeFormat)
    PlayingDateTime = PlayingDateTimeProperty(Either(ValidDateTimeFormat,ValidTimeFormat))
    PlayFrom = DateTimeFormatProperty(ValidTimeFormat)
    PlayedDuration = DateTimeFormatProperty(ValidTimeFormat)
    # ResumedOn = List[DateTimeFormatProperty(ValidTimeFormat)]



    def __init__(self, config, Video = None, PreviousVideo = None, NextVideo = None, PlayingDateTime = "", PlayFrom = "00:00:00", PlayedDuration = "00:00:00"):
        # super(VideoInAction, self).__init__()
        self._event = asyncio.Event()
        self.Video = Video
        self.PreviousVideo = PreviousVideo
        self.NextVideo = NextVideo
        self._PlayingDateTime = PlayingDateTime
        self.PlayFrom = PlayFrom
        self.PlayedDuration = PlayedDuration
        # at playing time
        # self.StartTime = StartTime
        # self.PlayingDateTime = PlayingDateTime
        # # self.EndTime = None
        # self._DisplayedTitle = None
        # # self._PlayingDateTime = None
        # self._ResumedTime = None
        # self._PlayingStatus = VideoStatus.NOTPLAYED

        # configure class variable: RTMPServerAddress
        address = config['RTMPServerAddress']['server_address']
        port = config['RTMPServerAddress']['server_port']
        tail = config['RTMPServerAddress']['tail']
        VideoInAction.setServerAddress(address, port, tail)
        self.config = config




    async def stream(self):
        # set PlayingDateTime class variable to trigger a watchdog
        self.PlayingDateTime = self._PlayingDateTime, self._event
        # wait till the date & time arrives
        await self._event.wait()
        print(f"Time to play {self.Video}")


    @classmethod
    def setServerAddress(cls, address, port, tail):
        if(cls.RTMPServerAddress == None):
            cls.RTMPServerAddress = f"rtmp://{address}:{port}{tail}"

    # @property
    # def StartTime(self):
    #     return self._StartTime

    # @property
    # def EndTime(self):
    #     return self._EndTime

    @property
    def DisplayedTitle(self):
        return self._DisplayedTitle

    # @property
    # def PlayingDateTime(self):
    #     return self._PlayingDateTime

    @property
    def ResumedTime(self):
        return self._ResumedTime

    @property
    def _PlayingStatus(self):
        return self._PlayingStatustus

    def set_start_end(self, startime:datetime.time = None, endtime:datetime.time = None):
        assert isinstance(startime, datetime.time), f"startime is not in time format, it is: {type(startime)} "
        assert isinstance(endtime, datetime.time), f"endtime is not in time format, it is: {type(endtime)} "
        self.StartTime = startime
        self.EndTime = endtime
    def set_display_title(self, display_title: str):
        assert isinstance(display_title, str), f"display_title is not in string format, it is: {type(display_title)} "
        self.DisplayedTitle = display_title

    def run(self):
        pass
    def pause(self):
        pass
    def stop(self):
        pass





