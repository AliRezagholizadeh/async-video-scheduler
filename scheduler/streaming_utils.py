import tempfile
import os
from pydub import AudioSegment
import subprocess
# from subprocess import PIPE
from scheduler.utils import ffmpegShellRun, run_ffmpeg
from pathlib import Path
import ffmpeg
import asyncio

STREAM_PROFILES = {
    "low": {
        "resolution": "854x480",
        "fps": 25,
        "bitrate": "700k",
        "maxrate": "700k",
        "bufsize": "1400k"
    },
    "medium": {
        "resolution": "1280x720",
        "fps": 30,
        "bitrate": "1500k",
        "maxrate": "1500k",
        "bufsize": "3000k"
    },
    "high": {
        "resolution": "1920x1080",
        "fps": 30,
        "bitrate": "3000k",
        "maxrate": "3000k",
        "bufsize": "6000k"
    }
}

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

    print("temp_audio_file: ", temp_audio_file)
    print("video_path: ", video_path)

    # extract and save the audio
    command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "copy", temp_audio_file]
    try:
        stderr, code = run_ffmpeg(command)
        # access to the saved audio by pydub

    except Exception as e:
        raise e
    else:
        if("Output file does not contain any stream" in stderr):
            audio_seg = None
            print("The video is SILENCE.")
        else:
            print(f"extract and save audio: code:{code}, err: {stderr}")
            audio_seg = AudioSegment.from_file(temp_audio_file, format=audio_format)

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

        print(f"deleting {temp_audio_file}")
        os.unlink(temp_audio_file)

    else: # clip is silent
        message = "Probable Warning: Clip is siltent.\n"
        current_dBFS = None




    return message, current_dBFS


async def async_to_rtmp_server(video_file_path:Path, rtmp_server_address):
    try:
        # out, err = ffmpeg.input(video_file_path, re=None).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run()
        # process = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', f='lavfi').input(str(video_file_path), re= None).output(rtmp_server_address, format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
        # process = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', f='lavfi')\
        #     .input(str(video_file_path), re= None)\
        #     .output(rtmp_server_address, format='flv', vcodec='libx264', c_v='copy', c_a='aac', shortest=None,)\
        #     .run_async(pipe_stdout=True, pipe_stderr=True)

        video_input = ffmpeg.input(str(video_file_path), **{'re': None})
        silent_audio = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', f='lavfi')

        # (
        process = ffmpeg.output(
            silent_audio, video_input,
            rtmp_server_address,
            format='flv',
            vcodec='libx264',
            # c_v='copy',
            # acodec='aac',
            # shortest=None
        ).run_async(pipe_stdout=True, pipe_stderr=True)
        # )
        # input_stream = ffmpeg.input(str(video_file_path))
        # process = input_stream.global_args('-re').output(rtmp_server_address, format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
        # process = ffmpeg.input("anullsrc=channel_layout=stereo:sample_rate=44100", str(video_file_path), "-re").output(rtmp_server_address, format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
        # process = ffmpeg.input(video_file_path, ss= "00:00:40").output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv', vcodec='libx264').run_async(pipe_stdout=True, pipe_stderr=True)
        # process = ffmpeg.input(video_file_path, re=None).output(f"rtmp://{self.server_address}:{self.server_port}/live/stream", format='flv').run_async(pipe_stdout=True, pipe_stderr=True)
         # "ffmpeg -i my_test_file.flv -c:v copy -c:a copy -f flv "rtmp://localhost:1935/live/stream
        process.wait()
        print(f"trigger_timely_video: video ({video_file_path}) streamed to the server ..")

        # print(f"trigger_timely_video: Error: {err},\n Out:{out}")
    except ffmpeg.Error as e:
        print(f"trigger_timely_video: An error occurred in loading video file to the server: {e}")

async def stream_to_rtmp_async_(video_file_path:Path, rtmp_server_address):
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-re",
        "-i", str(video_file_path),
        "-vf", "tpad=stop_mode=clone:stop_duration=5",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-c:a", "copy",
        "-ar", "44100",
        "-b:a", "128k",
        "-f", "flv",
        rtmp_server_address,
        stdout = asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )

    # Stream logs from FFmpeg in real time (optional)
    async for line in process.stderr:
        print(line.decode().strip())

    return await process.wait()

async def stream_to_rtmp_async(video_file_path:Path, rtmp_server_address, profile = "medium"):
    # ffmpeg command with consideration of 10 seconds OBS DELAY to connect
    settings = STREAM_PROFILES[profile]
    width, height = settings["resolution"].split("x")
    fps = str(settings["fps"])
    fps = "25"
    # ratio = 1.7
    ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-copyts",
        "-start_at_zero",
        "-f", "lavfi",
        "-i", "color=color=black:s=1280x720:r=30:d=5",  # 5s preroll
        "-i", str(video_file_path),
        "-filter_complex",
        "[1:v]scale=1280:720,fps=30,format=yuv420p,setsar=1,"
        "tpad=stop_mode=clone:stop_duration=10[v1];"
        "[0:v][v1]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-map", "1:a?",  # optional audio stream
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-b:v", "1500k",
        "-maxrate", "1500k",
        "-bufsize", "3000k",
        "-c:a", "aac",
        "-ar", "44100",
        "-b:a", "128k",
        "-r", "30",
        "-g", "60",
        "-keyint_min", "30",
        "-sc_threshold", "0",
        "-threads", "1",
        "-muxdelay", "0.5",
        "-f", "flv",
        rtmp_server_address,
    ]
    process = await asyncio.create_subprocess_exec(*ffmpeg_cmd, stdout = asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE)
    # process = await asyncio.create_subprocess_exec(
    #     "ffmpeg",
    #     "-re",
    #     "-f", "lavfi",
    #     "-i", f"color=color=black:s={settings['resolution']}:r={fps}:d=5",
    #     "-i", str(video_file_path),
    #     "-filter_complex",
    #     # f"[1:v]scale={width}:{height},fps={fps},format=yuv420p,setsar=1[v1];"
    #     f"[1:v]scale={width}:{height}, fps={fps},format=yuv420p,setsar=1,tpad=stop_mode=clone:stop_duration=10[v1]; [0:v][v1]concat=n=2:v=1:a=0[outv]",
    #     # f"[1:v]scale={width}:{int(int(width)/ratio)},fps={fps},format=yuv420p;"
    #     # f"[0:v][v1]concat=n=2:v=1:a=0[outv]",
    #     "-map", "[outv]",
    #     "-c:v", "libx264",
    #     "-preset", "veryfast",
    #     "-tune", "zerolatency",
    #     "-b:v", settings["bitrate"],
    #     "-maxrate", settings["maxrate"],
    #     "-bufsize", settings["bufsize"],
    #     "-r", fps,
    #     "-g", str(int(fps) * 2),
    #     "-keyint_min", fps,
    #     "-sc_threshold", "0",
    #     "-threads", "1",
    #     "-f", "flv",
    #     # rtmp_server_address,
    #     f"{video_file_path.parents[0]}/output.flv",
    #     stdout = asyncio.subprocess.DEVNULL,
    #     stderr=asyncio.subprocess.PIPE
    # )

    await process.wait()
    # Stream logs from FFmpeg in real time (optional)
    async for line in process.stderr:
        print(line.decode().strip())



async def twoStage_stream_real_time_pipeline(video_file_path:Path, rtmp_server_address, pre_time="0", post_time="0", stream_started_signal: asyncio.Event = None):
    # first_ffmpeg_cmd = [
    #     "ffmpeg",
    #     "-i", str(video_file_path),
    #     "-f", "mpegts",
    #     # "-filter_complex", "[0:v]scale=1280:720,fps=30,format=yuv420p[v];setsar=1[v1]",
    #     "-filter_complex", "[0:v]scale=1280:720,format=yuv420p[v]",
    #     "-map", "[v]",
    #     "-map", "0:a",
    #     "-c:v", "libx264",
    #     "-preset", "veryfast",
    #     "-b:v", "1500k",
    #     "-f", "flv",
    #     "pipe:1",
    # ]
    first_ffmpeg_cmd = [
        "ffmpeg",
        "-re",
        "-copyts",
        "-start_at_zero",
        "-f", "lavfi",
        "-i", f"color=color=black:s=1280x720:r=30:d={pre_time}",  # 5s preroll
        "-i", str(video_file_path),
        "-filter_complex",
        "[1:v]scale=1280:720,fps=30,format=yuv420p,setsar=1,"
        f"tpad=stop_mode=clone:stop_duration={post_time}[v1];"
        "[0:v][v1]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-map", "1:a?",  # optional audio stream
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-b:v", "1500k",
        "-maxrate", "1500k",
        "-bufsize", "3000k",
        "-c:a", "aac",
        "-ar", "44100",
        "-b:a", "128k",
        "-r", "30",
        "-g", "60",
        "-keyint_min", "30",
        "-sc_threshold", "0",
        "-threads", "1",
        "-muxdelay", "0.5",
        "-f", "flv",
        "pipe:1",
    ]
    first = await asyncio.create_task(asyncio.create_subprocess_exec(
        *first_ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    ))

    second = await asyncio.create_task(asyncio.create_subprocess_exec(
        "ffmpeg",
        "-re",
        "-i", "pipe:0",
        "-c", "copy",
        "-f", "flv",
        rtmp_server_address,
        stdin=asyncio.subprocess.PIPE,
        # stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    ))

    async def pipe_output(input_stream, output_stream):
        first_data = True
        while True:
            chunk = await input_stream.read(4096)
            if(first_data):
                print("chunk: ", chunk)
                if(stream_started_signal):
                    stream_started_signal.set()
                first_data = False
            if not chunk:
                output_stream.write_eof()
                break
            output_stream.write(chunk)
            await output_stream.drain()
    # Optionally print logs
    async def log_stream(stream, name):
        async for line in stream:
            print(f"{name}: {line.decode().strip()}")

    try:
        await asyncio.gather(
            pipe_output(first.stdout, second.stdin),
            log_stream(first.stderr, "ENCODE"),
            log_stream(second.stderr, "STREAM"),
            first.wait(),
            second.wait()
        )
    finally:
        if first.returncode is None:
            first.terminate()
        if second.returncode is None:
            second.terminate()
        await asyncio.gather(
            first.wait(),
            second.wait()
        )



async def stream_with_silent_audio_async(input_path, rtmp_url):
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-re",
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-i", str(input_path),
        "-shortest",
        "-c:v", "copy",
        "-c:a", "copy",
        # "-map", "1:v:0",    # use video from 2nd input (input_path)
        # "-map", "1:a:0?",   # use audio from 2nd input if present
        # "-map", "0:a:0",    # fallback to silent audio (anullsrc)
        # "-filter_complex", "[1:a:0][0:a:0]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        # "-map", "[aout]",   # use the mixed audio output
        "-f", "flv",
        rtmp_url,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )

    # Stream logs from FFmpeg in real time (optional)
    async for line in process.stderr:
        print(line.decode().strip())

    return await process.wait()