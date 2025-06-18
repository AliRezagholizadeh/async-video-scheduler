# TODO: Compelete VIDEO and VIDEOINACTION classes by completing its properties and Descriptors.
import asyncio
import datetime
from itertools import product
from pathlib import Path
import subprocess



VALID_VIDEO_FORMAT = [".mp4"]

TIME_FORMATS = ["%H:%M:%S.%f", "%H:%M:%S"]
DATE_FORMATS = ["%Y-%m-%d"]





def ValidTimeFormat(timestr: str, required = True):
    """
    Parameters:
        value: str format of the time
    Returns:
        datetime.time format of the input value
    """
    # value should be in TIME_FORMATS format
    # cast str to a predefined valid time format..
    raised_error = ""
    time = None
    for timeformat in TIME_FORMATS:
        try:
            time = datetime.datetime.strptime(timestr, timeformat).time()
            # print("timestr: ", timestr, "to time: ", time)

            raised_error = ""
            break
        except Exception as e:
            raised_error += f"Video length ({timestr}) should be in {timeformat} format. {e}\n"
            continue

    if (required and raised_error):
        raise ValueError(f"Video length ({timestr}) should be in {timeformat} format.")

    return time

def ValidDateTimeFormat(datetimestr: str, required = True):
    """
    Parameters:
        value: str format of the time
    Returns:
        datetime.time format of the input value
    """
    # value should be in TIME_FORMATS format
    # cast str to a predefined valid time format..
    raised_error = ""
    datetime_obj = None
    for datetimetup in product(DATE_FORMATS, TIME_FORMATS):
        datetimeformat = f"{datetimetup[0]} {datetimetup[1]}"
        # print("datetimeformat: ", datetimeformat)
        try:
            datetime_obj = datetime.datetime.strptime(datetimestr, datetimeformat)
            # print("datetimestr: ", datetimestr, "to datetime: ", datetime)
            # print("datetime: ", datetime_obj)
            raised_error = ""
            break
        except Exception as e:
            raised_error += f"Datetime ({datetimestr}, str: {isinstance(datetimestr, str)}) should be in {datetimeformat} format. {e}\n"
            continue

    if (required and raised_error):
        raise ValueError(f"{raised_error} \n")

    return datetime_obj


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

        time_value = self.validfunc(value, required =False)
        instance.__dict__[self.property_name] = time_value



class PlayingDateTimeProperty:

    def __init__(self, validfunc):
        self.validfunc = validfunc

    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__.get(self.property_name) or None

    # def __set__(self, instance, value, event):
    def __set__(self, instance, values):
        # print("values: ", values)
        assert len(values) == 2, "the value should also contain asyncio.Event() variable."
        value, event = values
        if not isinstance(value, str):
            raise ValueError(f'The {self.property_name} must be a string')

        time_value = self.validfunc(value)

        assert time_value, f"playing time {value} is not recognized."
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
    if(not isinstance(scheduled_date_time, (datetime.datetime, datetime.time))):
        raise f"schedule date/time (i.e. {scheduled_date_time}) is not recognized. it's type: {type(scheduled_date_time)}"


    while True:
        current = datetime.datetime.now
        if (isinstance(scheduled_date_time, datetime.time)):
            current = datetime.datetime.now().time

        if(current() >= scheduled_date_time):
            #TODO: play the right timeslot of the video
            print(f"trigger_watchdog: It's time to set the event. current: {current()}, scheduled_date_time: {scheduled_date_time}")
            try:
                event.set()
                break
                # print(f"trigger_timely_video: Error: {err},\n Out:{out}")
            except Exception as e:
                print(f"trigger_watchdog: An error occurred in its setting: {e}")
        else:
            print(f"now: {current()}, scheduled_time: {scheduled_date_time}. So trigger_watchdog is waiting the time arrive..")

            # await asyncio.sleep((scheduled_date_time - datetime.datetime.now().time()).seconds)
            await asyncio.sleep(0.5)


def Either(*validationFuncs):
    def validate(value):
        for validfunc in validationFuncs:
            if((result:=validfunc(value, required = False))):
                return result

        return False
    return validate


def ffmpegShellRun(ffmpeg_command):
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = process.communicate()
        retcode = process.returncode
    except Exception as e:
        raise Exception(f"Error in running ffmpeg command over shell: {e}")

    return out, err, retcode

def run_ffmpeg(command_list):
    try:
        result = subprocess.run(
            command_list,
            stderr=subprocess.PIPE,
            # check=True
        )
        return result.stderr.decode(), 0  # returning stderr and success code
    except subprocess.CalledProcessError as e:
        return e.stderr.decode(), e.returncode




class CurrentDTimeProperty:
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        # instance.__dict__[self.property_name] = datetime.datetime.now().strftime(f"{DATE_FORMATS[0]} {TIME_FORMATS[0]}")
        current = datetime.datetime.now()
        current_ = datetime.datetime.now().strftime(f"{DATE_FORMATS[0]} {TIME_FORMATS[0]}")

        return current, current_



class MainClock:
    """Main clock which is going to trigger pulses in every 1/frequency second with the help of its _event."""
    _instance = None
    _event = None

    def __init__(self, frequency = 1):
        """frequency of triggering the event in each second."""
        self.frequency = frequency

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # cls._instance = super().__new__(cls, *args, **kwargs)
            cls._event = asyncio.Event()
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    async def timer(self):
        while(True):

            await asyncio.sleep(1/self.frequency)
            if(not self._event.is_set()):
                self._event.set()
                # print(">> CLOCK-level: event is set. So the worker is able to use it..")

            else:
                print("!!! CLOCK-level: event is not cleared. So the worker has not used..")

    def get_event(self):
        assert isinstance(self._event, asyncio.Event), f"Clock event is: {self._event}"
        # print("clock event: ", self._event)
        return self._event


class CLOCKProperty:
    def __set_name__(self, owner, name):
        self.property_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Instantiate from the MainClock
        clock = MainClock()
        # print("main clok set..")
        return clock


