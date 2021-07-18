#!/usr/bin/env python
"""
useful links:

https://stackoverflow.com/questions/48483348/how-to-limit-concurrency-with-python-asyncio
https://docs.python.org/3/library/asyncio-task.html#waiting-primitives

https://stackoverflow.com/questions/636561/how-can-i-run-an-external-command-asynchronously-from-python
https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/
"""


import asyncio
import sys
import time

from enum import Enum
from dataclasses import dataclass
from typing import Callable, List


usage = """
crun - Run commands in a chain and concurrently
    
USAGE:
    
    crun OPTIONS...
OPTIONS:
    -c STRING    Add a concurrent command
    -s STRING    Add a sequential command
    -n INT       Maximum concurrency (threads number) [CPUs number]
    -stdin       Concurrently run commands from STDIN
    -h           Help message
    
NOTE:
    The order of options decides the work flow! The two cases below are different:
    
    crun -s ls -s date
    crun -s date -s ls
EXAMPLE:
    crun -n 4 -s job1 -c job2 -c job3 -c job4 -s job5 -s job6
    The work flow is: 
        1. job1 must be executed fist. 
        2. job2,3,4 are independent, so they could be executed parallelly.
        3. job5 must wait for job2,3,4 being done.
        4. job6 could not start before job5 done.
     
    See the workflow graph below, long arrow means long excution time.
        
                  |----> job2     |  
        job1 ---> |---> job3      | -------> job5 ---> job6
                  |--------> job4 |

    actual examples:
    λ ./crun.py -n 3 -s "echo started"  -c "python sleeper.py 1 1 5" -c "python sleeper.py 2 131 133" -c "echo hahaha" -c "ls /zzz" -c "date" -s "echo done"
    λ cat jobs.list | ./crun.py -n 8 -s "echo start" -stdin -s "echo done"
    λ cat jobs.list | ./crun.py -n 2 -stdin
"""


class Kind(Enum):

    SEQUENTIAL   = 1
    PARALLELIZED = 2

Command = str

@dataclass
class Job:

    kind: Kind
    cmds: List[Command]


async def gather_with_concurrency(n, *tasks):
    """
    Using semaphores to concurrently run at max n
    coroutines alone.
    """

    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def _read_stream(stream: asyncio.StreamReader, ss_callback: Callable):
    """
    supposed to read every output/err stream and
    apply the callback on it. But it doesn't work
    afaik, it still outputs stuff everything in the end.
    """
    
    while True:
        line = await stream.readline()
        if line:
            ss_callback(line)
        else:
            break



async def run(command: str):
    """
    asyncio subprocess shell execution of a command.
    """

    print(f"Running {command = } ...")
    start_time = time.time()
    proc = await asyncio.subprocess.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    await asyncio.wait([
        _read_stream(proc.stdout, lambda x: print(f"[stdout]-[{command}] := {x.decode()}", end="")),
        _read_stream(proc.stderr, lambda x: print(f"[stderr]-[{command}] := {x.decode()}", end="")),
    ])

    exit_code = await proc.wait()
    finish_time = time.time()
    print(f"Finished running {command = } it returned {exit_code = }, took {round(finish_time - start_time, 2)} seconds.\n")


async def init() -> List[Job]:
    """
    passes command line arguments,
    converts them into jobs.
    """

    args = sys.argv[1:]
    nargs = len(args)

    type_help_str = "\nType -h for help\n"
    if nargs < 1:
        print(type_help_str)
        sys.exit(0)


    jobs : List[Job] = []

    i = 0
    max_coro = 4
    flag, value = "", ""

    while i < nargs:

        flag = args[i]
        i += 1

        if flag in ["-h", "-help", "--help"]:
            print(usage)
            sys.exit(0)

        elif flag == "-stdin":
            stdin = sys.stdin.read()
            stdin_conc_jobs = list(filter(None, stdin.split("\n")))
            converted_stdin_conc_jobs = []

            for scj in stdin_conc_jobs:
                converted_stdin_conc_jobs.append("-c")
                converted_stdin_conc_jobs.append(scj)

            args = args[:i] + converted_stdin_conc_jobs + args[i:]
            nargs = len(args)
            continue

        elif not flag.startswith("-"):
            print(f"invalid option: {flag}")
            sys.exit(1)

        if i >= nargs:
            print(f"no value for {flag}")
            sys.exit(1)

        value = args[i]
        i += 1

        if flag == "-n":
            max_coro = int(value)
            print(f"Setting maximum concurrent coroutines to {max_coro} ...")

        elif flag == "-s":
            jobs.append(Job(Kind.SEQUENTIAL, [value]))

        elif flag == "-c":

            if jobs:
                prev_job = jobs[-1]

                if prev_job.kind == Kind.PARALLELIZED:
                    prev_job.cmds.append(value)
                else:
                    jobs.append(Job(Kind.PARALLELIZED, [value]))

            else:
                jobs.append(Job(Kind.PARALLELIZED, [value]))

    return jobs, max_coro



async def main():
    
    jobs, max_coro = await init()

    for job in jobs:

        if job.kind == Kind.SEQUENTIAL:
            cmd = job.cmds[0]
            await run(cmd)
        else:
            await gather_with_concurrency(max_coro, *(run(cmd) for cmd in job.cmds))


if __name__ == "__main__":
    asyncio.run(main())
