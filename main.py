import asyncio
import json
import yaml
import datetime
from scheduler.core import program_pipeline
from server.utils import RTMP_Server
TIME_FORMAT = "%H:%M:%S"


async def main():
    # LOAD
    # load program schedule and config
    schedule_file = "schedule.json"
    with open(schedule_file, "r") as f:
        schedule = json.load(f)


    # change some time variables to let us test the program now
    schedule["program_schedule"]["start_time"] = (start:= datetime.datetime.now() + datetime.timedelta(seconds = 10)).time()
    for ontime_indx in range(len((ontime_contents:= schedule["program_schedule"]["on-time_contents"]))):
        if(ontime_contents[ontime_indx]["name"] == "start_program"):
            ontime_contents[ontime_indx]["play_time"]= start.time()
        else:
            ontime_contents[ontime_indx]["play_time"] = (start + datetime.timedelta(seconds= 20)).time()

    print(f"{'-'*10}\nschedule: \n{schedule} \n{'-'*10}")
    # load config
    config_file = "config.yaml"
    with open(config_file, 'r') as confile:
        config = yaml.safe_load(confile)
    print(f"config: \n{config} \n{'-'*10}")
    # access to the videos to play to build a streaming pipeline
    source_dir = config["program_source_path"]["video"]
    print(f"config type: {type(config)}")


    medimtx = RTMP_Server(config)
    end_program_siganl = asyncio.Event()
    server_task = asyncio.create_task(medimtx.run())
    process = await server_task

    i = 0
    while(not medimtx.is_mediamtx_running() or not medimtx.has_active_stream()): # RTMP server is not running or pushing the stream
        print(f"\rWait till the MediaMTX server be launched {('.')*(i%20)}")
        i += 1
        await asyncio.sleep(2)

    print("MediaMTX Server is checked being running .. ")
    program = program_pipeline(config=config, program_schedule=schedule)
    # server_task = asyncio.create_task(program.run_server())
    schedule_task = asyncio.create_task(program.set_run_schedule())



    print("main: awaiting schedule_task")
    await schedule_task
    print("main: program ended")



    # await server_task
    # each time a specific time-frame of the stream is loaded
    # start to play at a certain time with ability to find right time to play in the case of interruption.

    #
    print("server is waiting the program be terminated.")
    end_program_siganl.set()
    process.terminate()
    # if process.returncode is None:
    #     process.terminate()
    print("Program finished.")



if __name__ == "__main__":
    asyncio.run(main())