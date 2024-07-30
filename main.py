from fastapi import FastAPI

from threading import Event, Thread

import uvicorn
import time


app = FastAPI()
count_of_threadings = 10
events: list[Event] = [Event()] * count_of_threadings
threads: list[Thread] = [None] * count_of_threadings
counter = [0] * count_of_threadings


def counter_threadings(index):
    while not events[index].is_set():
        counter[index] += 1
        print(f"Счетчик {index+1} на значении {counter[index]}")
        time.sleep(1)

@app.get("/start/")
async def start_threadings():
    messages = []
    for index in range(count_of_threadings):
        if threads[index] is None or not threads[index].is_alive():
            events[index].clear()
            threads[index] = Thread(target=counter_threadings, args=(index, ))
            threads[index].start()
            messages.append(f"Счетчик {index+1} стартовал")
        else:
            messages.append(f"Счетчик {index+1} уже запущен")

    return {
        "messages": messages
    }

@app.get("/stop/")
async def stop_threadings():
    for index in range(count_of_threadings):
        events[index].set()
    return {
        "messages": "Все потоки остановлены"
    }

@app.get("/status/")
async def status_threadings():
    messages = {"counter": []}
    messages["counter"] = [{"id": index+1, "value": counter[index], "running": not events[index].is_set()} for index in range(count_of_threadings)]

    return {
        "messages": messages
    }

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)