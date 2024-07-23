import multiprocessing
import os
import time
import random
 
def calc(val1, val2):
    sleep = random.randint(0, 5)
    time.sleep(sleep)
    print(f"Init Process ID: {os.getpid()}, calculating: {val1} + {val2} with sleep {sleep}")
    return val1 + val2
 
def main():
    pool = multiprocessing.Pool(7)
    input_data = [(i, 0) for i in range(20)]
    print("input data:", input_data)
 
    results = pool.starmap(calc, input_data)
    pool.close()
    pool.join()
 
    print("output data:", results)
 
if __name__ == "__main__":
    main()