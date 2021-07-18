# crun

Run workflow. Generally all parts are sequential executed, and some parts could be done parallelly.



## Usage
   
    ./crun.py OPTIONS...

    OPTIONS:

        -c STRING    Add a concurrent command
        -s STRING    Add a sequential command
        -n INT       Maximum concurrency (default 4)
        -stdin       Concurrently run commands from STDIN
        -h           Help message
        
Note: The order of options decides the work flow! The two cases below are different:
    
    ./crun.py -s ls -s date
    ./crun.py -s date -s ls


Example:

    
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
     
You can also concurrently run commands from STDIN:

    cat jobs.list | ./crun.py -t 8 -s "echo start" -stdin -s "echo end" 
    

More examples:

```bash
    ./crun.py -n 3 -s "echo started"  -c "python sleeper.py 1 1 5" -c "python sleeper.py 2 131 133" -c "echo hahaha" -c "ls /zzz" -c "date" -s "echo done"
```

```bash
    cat jobs.list | ./crun.py -n 2 -stdin
```


## Credits

This work (including README) is a shameless ripoff of [shenwei/crun](https://github.com/shenwei356/crun) Golang & Perl implementation of solving the problem. I tried to solve the same using Python's [asyncio](https://docs.python.org/3/library/asyncio.html).


## Learnings

* I wanted to take this as a challenge to compare and see how easy/bloody difficult it is to implement concurrent program in Python against Golang. It was easier than I expected but failed at few objectives.
* I tried my best to get Subprocess's STDOUT and STDERR streaming. I tried stuff mentioned over [here](https://stackoverflow.com/questions/636561/how-can-i-run-an-external-command-asynchronously-from-python), [here](https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/) and [here](https://trio.readthedocs.io/en/stable/reference-io.html#trio.open_process) but gave up. meh.
* [asyncio.Semaphore](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore) was a new thing, I had to use it to control the number of parallel coroutines for the parallel/concurrent jobs while gathering.
* It's way easier to solve a problem when somebody already solved it. :P. Thanks shenwei.



### Sample Demos

```bash
λ ./crun.py -s "echo started" -c "ls" -c "date" -s "echo done"
Running command = 'echo started' ...
[stdout]-[echo started] := started
Finished running command = 'echo started' it returned exit_code = 0, took 0.02 seconds.

Running command = 'ls' ...
Running command = 'date' ...
[stdout]-[ls] := README.md
[stdout]-[ls] := crun.py
[stdout]-[ls] := jobs.list
[stdout]-[ls] := sleeper.py
Finished running command = 'ls' it returned exit_code = 0, took 0.03 seconds.

[stdout]-[date] := Sun Jul 18 17:02:59 IST 2021
Finished running command = 'date' it returned exit_code = 0, took 0.03 seconds.

Running command = 'echo done' ...
[stdout]-[echo done] := done
Finished running command = 'echo done' it returned exit_code = 0, took 0.01 seconds.
```

```bash
λ cat jobs.list | ./crun.py -n 2 -stdin

Setting maximum concurrent coroutines to 2 ...
Running command = 'echo started' ...
Running command = 'seq 1 200' ...
[stdout]-[echo started] := started
Finished running command = 'echo started' it returned exit_code = 0, took 0.02 seconds.

Running command = 'python sleeper.py 1 1 5' ...
[stdout]-[seq 1 200] := 1
[stdout]-[seq 1 200] := 2
...
[stdout]-[seq 1 200] := 199
[stdout]-[seq 1 200] := 200
Finished running command = 'seq 1 200' it returned exit_code = 0, took 0.02 seconds.

Running command = 'echo haha' ...
[stdout]-[echo haha] := haha
Finished running command = 'echo haha' it returned exit_code = 0, took 0.01 seconds.

Running command = 'python sleeper.py 2 131 133' ...
[stdout]-[python sleeper.py 2 131 133] := proc_id = '2' :: i = 131
[stdout]-[python sleeper.py 2 131 133] := proc_id = '2' :: i = 132
[stdout]-[python sleeper.py 2 131 133] := proc_id = '2' :: i = 133
Finished running command = 'python sleeper.py 2 131 133' it returned exit_code = 0, took 3.05 seconds.

Running command = 'seq 15 20' ...
[stdout]-[seq 15 20] := 15
[stdout]-[seq 15 20] := 16
[stdout]-[seq 15 20] := 17
[stdout]-[seq 15 20] := 18
[stdout]-[seq 15 20] := 19
[stdout]-[seq 15 20] := 20
Finished running command = 'seq 15 20' it returned exit_code = 0, took 0.03 seconds.

Running command = 'ls -lh' ...
[stdout]-[ls -lh] := total 12K
[stdout]-[ls -lh] := -rw-r--r-- 1 greyhound greyhound 3.4K Jul 18 17:06 README.md
[stdout]-[ls -lh] := -rwxr-xr-x 1 greyhound greyhound 5.5K Jul 18 16:44 crun.py
[stdout]-[ls -lh] := -rw-r--r-- 1 greyhound greyhound  117 Jul 18 16:21 jobs.list
[stdout]-[ls -lh] := -rw-r--r-- 1 greyhound greyhound  246 Jul 18 12:58 sleeper.py
Finished running command = 'ls -lh' it returned exit_code = 0, took 0.02 seconds.

Running command = 'date' ...
[stdout]-[date] := Sun Jul 18 17:06:23 IST 2021
Finished running command = 'date' it returned exit_code = 0, took 0.02 seconds.

Running command = 'echo done' ...
[stdout]-[echo done] := done
Finished running command = 'echo done' it returned exit_code = 0, took 0.01 seconds.

[stdout]-[python sleeper.py 1 1 5] := proc_id = '1' :: i = 1
[stdout]-[python sleeper.py 1 1 5] := proc_id = '1' :: i = 2
[stdout]-[python sleeper.py 1 1 5] := proc_id = '1' :: i = 3
[stdout]-[python sleeper.py 1 1 5] := proc_id = '1' :: i = 4
[stdout]-[python sleeper.py 1 1 5] := proc_id = '1' :: i = 5
Finished running command = 'python sleeper.py 1 1 5' it returned exit_code = 0, took 5.05 seconds.
```
