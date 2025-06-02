import tempfile
import os
from pydub import AudioSegment
import subprocess
# from subprocess import PIPE
from scheduler.utils import ffmpegShellRun, run_ffmpeg
from pathlib import Path
import ffmpeg


def adjust_volume(video_path: Path, potTargetdBFS):
    '''
    Parameters:
        video_path
        potTargetdBFS: potential target dBFS is a dBFS which is going to adjust the video sound upon that if it's current
         volume is above -1 dBFS.
    :return:
    '''
    audio_format = "m4a"
    # audio_file = f"audio.{audio_format}"
    # it adjusts a audio of a video to have acceptable volume.
    # create a temporal file
    # with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as temp_audio_file_:
    #     temp_audio_file = temp_audio_file_.name
    video_name = str(video_path.name).split('.')[0]
    temp_audio_file = f"{video_path.parents[0]}/audio_{video_name}.{audio_format}"
    # It seems we can use RAM for temp file for more speed..

    # print("temp_audio_file: ", temp_audio_file.name)
    print("temp_audio_file: ", temp_audio_file)
    print("video_path: ", video_path)
    # extract and save the audio
    # ffmpeg_command = f"ffmpeg -i '{str(video_path)}' -vn -acodec copy {str(temp_audio_file.name)}"
    # out, err, retcode = ffmpegShellRun(ffmpeg_command)
    # command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "copy", str(temp_audio_file.name)]
    command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "copy", temp_audio_file]
    stderr, code = run_ffmpeg(command)

    print(f"extract and save audio: code:{code}, err: {stderr}")

    # if(retcode!=0):
    #     raise Exception("Error in extract and save audio using ffmpeg shell command.")
    # access to the saved audio by pydub
    audio_seg = AudioSegment.from_file(temp_audio_file, format = audio_format)

    if(audio_seg != None):
        # Get the current dBFS (decibels Full Scale)
        current_dBFS = audio_seg.dBFS

        # adjust the volume if is above -1 dBFS
        message = ""
        if (current_dBFS > -1):
            # Calculate the gain needed to reach the new dBFS
            gain_needed = potTargetdBFS - current_dBFS

            # Apply the gain
            modified_audio = audio_seg.apply_gain(gain_needed)

            message = f"The base sound strength of {current_dBFS} is adjusted to {modified_audio.dBFS}.\n"
            current_dBFS = modified_audio.dBFS
            # store adjusted audio:
            modified_audio.export(temp_audio_file, format= audio_format)

            # ffmpeg to modify the video sound
            # replace_ffmpeg_command = f"ffmpeg -i '{video_path}' -i {temp_audio_file.name} -c:v copy -map 0:v:0 -map 1:a:0 -shortest {video_path}"
            # out, err, retcode = ffmpegShellRun(replace_ffmpeg_command)
            command = ["ffmpeg", "-i", video_path, "-i", temp_audio_file, "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", temp_audio_file.name]
            stderr, code = run_ffmpeg(command)
            print(f"replacing adjusted audio: code:{code}, err: {stderr}")
            # if (retcode != 0):
            #     raise Exception("Error in replacing adjusted audio using ffmpeg shell command.")

        else:
            message = f"Current volume ({current_dBFS}) is already acceptable."


    else: # clip is silent
        message = "Probable Warning: Clip is siltent.\n"
        current_dBFS = None

    print(f"deleting {temp_audio_file}")
    os.unlink(temp_audio_file)


    return message, current_dBFS


async def async_to_rtmp_server(video_file_path:Path, rtmp_server_address):
    try:
        # out, err = ffmpeg.input(video_file_path, re=None).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run()
        process = ffmpeg.input(str(video_file_path)).output(rtmp_server_address, format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
        # process = ffmpeg.input(video_file_path, ss= "00:00:40").output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
        # process = ffmpeg.input(video_file_path, re=None).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv').run_async(pipe_stdout=True, pipe_stderr=True)
         # "ffmpeg -i my_test_file.flv -c:v copy -c:a copy -f flv "rtmp://localhost:1935/live/stream
        print(f"trigger_timely_video: video ({video_file_path}) streamed to the server ..")
        process.wait()
        # print(f"trigger_timely_video: Error: {err},\n Out:{out}")
    except ffmpeg.Error as e:
        print(f"trigger_timely_video: An error occurred in loading video file to the server: {e}")
