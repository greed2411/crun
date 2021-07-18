import time
import sys

if __name__ == "__main__":
    
    args = sys.argv[1:]
    proc_id = args[0]
    low = int(args[1])
    high = int(args[2])

    for i in range(low, high+1):
        print(f"{proc_id = } :: {i = }")
        time.sleep(1)
