# async-video-scheduler

Did you think of launching a timely video player which is streaming a source of videos at specified times?

This event-based tool aim at timely streaming from an ordered-video source. In the case of disconnection, the frames would be streamed
from the point when there wasn't any interruption.

### Architecture Diagram

[Python Controller]
     ↓ select
 local video / streams
     ↓
   [FFmpeg] ←  [rolling.txt / overlay triggers] ← updates [Python Controller]
     ↓ sends live video
    [RTMP server (rtmp://localhost:1935/live/stream): using MediaMTX]
    
In parallel:

[OBS (Media Source)]
 ↓ monitor the stream
[RTMP server (rtmp://localhost:1935/live/stream):]
↓ preview & out
[OBS RTMP Output]
 ↓
[YouTube or Custom RTMP Server]










### Step-by-Step: Setup MediaMTX as a Local RTMP Server
#### Step 1: Download and Install MediaMTX
Go to: 👉 https://github.com/bluenviron/mediamtx/releases

Download the appropriate binary for your OS:

- Windows: mediamtx.exe

- macOS/Linux: mediamtx

Unzip and place the binary in a known folder.
```
mediamtx/
├── mediamtx         # binary
├── mediamtx.yml     # config file
```

#### Step 2: Default Configuration (No Change Needed)
MediaMTX uses mediamtx.yml as its config file, but the default config needs to be adjusted to enable RTMP at rtmp://localhost:1935/live/stream.

Adjust `paths` section of the config file to:
```
paths:
  all:
    source: publisher # accept streams from FFmpeg or OBS
```

#### Step 3: Run MediaMTX
In your terminal:
```bash
./mediamtx
```
You should see:
```nginx
INF RTMP listener opened on :1935
```
MediaMTX is now acting as a local RTMP server.



### Stream to MediaMTX from FFmpeg
Base ffmpeg command used to pass the right video to the RTMP server:
```commandline
ffmpeg -re -i input.mp4 -f flv rtmp://localhost:1935/live/stream
```
which `input` could be a dynamic pipeline (e.g., using overlays or named pipes).




### Configuring OBS to Watch the Stream
1- Open OBS

2- Add a new Media Source

3- Uncheck Local File

4- Set the URL to:
`rtmp://localhost:1935/live/stream`


5- (Optional) Set Buffering to 0 for lowest latency

OBS will now display your FFmpeg stream in real time.





Required:
- opencv-python-4.11.0.86
- moviepy-2.2.1
- pydub-0.25.1