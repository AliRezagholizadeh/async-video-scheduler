import asyncio
import json
import yaml
import datetime
from scheduler.core import program_pipeline, Program, Program_core
from server.utils import RTMP_Server
from scheduler.utils import TIME_FORMATS, DATE_FORMATS


async def main():
    # LOAD
    # load program schedule and config
    # load config
    config_file = "config.yaml"
    with open(config_file, 'r') as confile:
        config = yaml.safe_load(confile)
    print(f"config: \n{config} \n{'-' * 10}")
    # access to the videos to play to build a streaming pipeline
    video_source_dir = config["program_source_path"]["video"]
    print(f"config type: {type(config)}")

    program_name = "Daily_Contents/Day1"
    # load program schedule
    schedule_file = video_source_dir + f"{program_name}/schedule.json"
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


    # Check RTMP server being active
    # TODO: check all possibilities might happen.
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
    # start_dtime = (datetime.datetime.now() + datetime.timedelta(seconds=10)).strftime(f"{DATE_FORMATS[0]} {TIME_FORMATS[0]}") #
    # print("start_dtime:" , start_dtime)


    program_args = {
        "root_program_path": video_source_dir + f"{program_name}/",
        "name": "sample_program"
    }
    # program = Program.create(**program_args)
    # program = next(Program.create(**program_args))
    # program_task = asyncio.create_task(program)
    # program_body = asyncio.create_task(Program.create(**program_args))
    # async for program in Program.create(**program_args):

    # schedule_task = asyncio.create_task(Program.create(**program_args))
    # program = next(program_body)

    # program = program_pipeline(config=config, program_schedule=schedule)
    # schedule_task = asyncio.create_task(program.set_run_schedule())

    # program_main = asyncio.create_task(Program.create(**program_args))
    # print(" >>> program created .. Now run it ..")
    # program_run = asyncio.create_task(program_main.result().run())

    # async with Program.create(**program_args) as program:
    async with Program_core(**program_args) as program:
        program_run = asyncio.create_task(program.run())

        print("main: awaiting run")
        await program_run
        print("main: awaiting program main clock")

    # await program_main
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