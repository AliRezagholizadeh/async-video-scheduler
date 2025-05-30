import tempfile
import os
from pydub import AudioSegment
import subprocess
# from subprocess import PIPE
from scheduler.utils import ffmpegShellRun
def adjust_volume(video_path, potTargetdBFS):
    '''
    Parameters:
        video_path
        potTargetdBFS: potential target dBFS is a dBFS which is going to adjust the video sound upon that if it's current
         volume is above -1 dBFS.
    :return:
    '''
    # it adjusts a audio of a video to have acceptable volume.
    # create a temporal file
    temp_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    # extract and save the audio
    ffmpeg_command = f"ffmpeg -i {video_path} -vn -acodec copy {temp_audio_file}"
    out, err, retcode = ffmpegShellRun(ffmpeg_command)
    print(f"extract and save audio: out:{out}, err: {err}")

    # if(retcode!=0):
    #     raise Exception("Error in extract and save audio using ffmpeg shell command.")
    # access to the saved audio by pydub
    audio_seg = AudioSegment.from_file(temp_audio_file)

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

            # store adjusted audio:
            modified_audio.export(temp_audio_file, format=".wav")

            # ffmpeg to modify the video sound
            replace_ffmpeg_command = f"ffmpeg -i {video_path} -i {temp_audio_file} -c:v copy -map 0:v:0 -map 1:a:0 -shortest {video_path}"
            out, err, retcode = ffmpegShellRun(ffmpeg_command)
            print(f"replacing adjusted audio: out:{out}, err: {err}")
            # if (retcode != 0):
            #     raise Exception("Error in replacing adjusted audio using ffmpeg shell command.")

        else:
            message = f"Current volume ({current_dBFS}) is already acceptable."


    else: # clip is silent
        message = "Probable Warning: Clip is siltent.\n"
    os.unlink(temp_audio_file.name)


    return message