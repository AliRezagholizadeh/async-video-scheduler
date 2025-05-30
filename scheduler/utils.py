# TODO: Compelete VIDEO and VIDEOINACTION classes by completing its properties and Descriptors.
import asyncio
import datetime
from itertools import product
from pathlib import Path

VALID_VIDEO_FORMAT = [".mp4"]

TIME_FORMATS = ["%H:%M:%S:%f", "%H:%M:%S"]
DATE_FORMATS = ["%Y-%m-%d"]





def ValidTimeFormat(timestr: str):
    """
    Parameters:
        value: str format of the time
    Returns:
        datetime.time format of the input value
    """
    # value should be in TIME_FORMATS format
    # cast str to a predefined valid time format..
    raised_error = ""
    for timeformat in TIME_FORMATS:
        try:
            time = datetime.datetime.strptime(timestr, timeformat)
            raised_error = ""
            break
        except Exception as e:
            raised_error += f"Video length ({timestr}) should be in {timeformat} format. {e}\n"
            continue

    if (raised_error):
        raise ValueError(f"Video length ({timestr}) should be in {timeformat} format. {e}")

    return time

def ValidDateTimeFormat(datetimestr: str):
    """
    Parameters:
        value: str format of the time
    Returns:
        datetime.time format of the input value
    """
    # value should be in TIME_FORMATS format
    # cast str to a predefined valid time format..
    raised_error = ""
    for datetimetup in product(DATE_FORMATS, TIME_FORMATS):
        datetimeformat = f"{datetimetup[0]} {datetimetup[1]}"
        try:
            datetime = datetime.datetime.strptime(datetimestr, datetimeformat)
            raised_error = ""
            break
        except Exception as e:
            raised_error += f"Video length ({datetimestr}) should be in {datetimeformat} format. {e}\n"
            continue

    if (raised_error):
        raise ValueError(f"Video length ({datetimestr}) should be in {datetimeformat} format. {e}")

    return datetime


class ReqDateTimeFormatProperty:
    def __init__(self, validfunc):
        self.validfunc = validfunc

    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise ValueError(f'The {self.property_name} must be a string')

        if len(value) == 0:
            raise ValueError(f'The {self.property_name} cannot be empty')

        time_value = self.validfunc(value)
        instance.__dict__[self.property_name] = time_value



class DateTimeFormatProperty:
    def __init__(self, validfunc):
        self.validfunc = validfunc
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise ValueError(f'The {self.property_name} must be a string')

        time_value = self.validfunc(value)
        instance.__dict__[self.property_name] = time_value



class PlayingDateTimeProperty:

    def __init__(self, validfunc):
        self.validfunc = validfunc

    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value, event):
        if not isinstance(value, str):
            raise ValueError(f'The {self.property_name} must be a string')

        time_value = self.validfunc(value)

        # launch timely watchdog with event
        asyncio.create_task(trigger_watchdog(time_value, event))

        instance.__dict__[self.property_name] = time_value


class ReqPATH:
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value):
        if(not value):
            raise ValueError(f"{self.property_name} is a required field and should get the video path.")

        if (isinstance(value, str)):
            value = Path(value)
        assert isinstance(value, Path), f"path format is not recognized. Type: ({type(value)})"
        assert value.is_file(), "There is not such video file."
        assert (format := value.suffix) in VALID_VIDEO_FORMAT, f"The video format is {format} which is not supported. All valid video formats are: {VALID_VIDEO_FORMAT}. "

        instance.__dict__[self.property_name] = value


class ReqField:
    def __init__(self, type):
        self.type = type
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__[self.property_name] or None

    def __set__(self, instance, value):
        if (not value):
            raise ValueError(f"{self.property_name} is a required field and should get a value.")

        assert isinstance(value, self.type), f" {self.property_name}'s format should be {self.type} but recognized: {type(value)}."

        instance.__dict__[self.property_name] = value


async def trigger_watchdog(scheduled_date_time: datetime.datetime, event):
    """
    Stands between the server and the local resources. It is set based on the scheduled time and video assigned.
    If time arrive, it will out the right timeslot of the video to the local RTMP server ran by the server method.

    """
    while True:

        if(datetime.datetime.now().time() >= scheduled_date_time):
            #TODO: play the right timeslot of the video
            print("trigger_watchdog: It's time to set the event.")
            try:
                event.set()
                break
                # print(f"trigger_timely_video: Error: {err},\n Out:{out}")
            except Exception as e:
                print(f"trigger_watchdog: An error occurred in its setting: {e}")

        else:
            print(f"now: {datetime.datetime.now().time()}, scheduled_time: {scheduled_date_time}. So trigger_watchdog is waiting the time arrive..")

            await asyncio.sleep(await asyncio.sleep((scheduled_date_time - datetime.datetime.now().time()).seconds))


def Either(*validationFuncs):
    def validate(value):
        for validfunc in validationFuncs:
            if((result:=validfunc(value))):
                return result

        return False
    return validate


import subprocess
def ffmpegShellRun(ffmpeg_command):
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    try:
        out, err = process.communicate()
        retcode = process.returncode
    except Exception as e:
        raise Exception(f"Error in running ffmpeg command over shell: {e}")

    return out, err, retcode
