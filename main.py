import asyncio
import json
import yaml
import datetime
from scheduler.core import program_pipeline
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
    program = program_pipeline(config=config, program_schedule=schedule)
    # server_task = asyncio.create_task(program.run_server())
    schedule_task = asyncio.create_task(program.set_run_schedule())

    print("main: awaiting schedule_task")
    await schedule_task
    print("main: awaiting server_task")
    await server_task
    # each time a specific time-frame of the stream is loaded
    # start to play at a certain time with ability to find right time to play in the case of interruption.

    #





if __name__ == "__main__":
    asyncio.run(main())