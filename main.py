from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from threading import Event, Thread

import uvicorn
import time
import asyncio


app = FastAPI()
templates = Jinja2Templates(directory="templates")
count_of_threadings = 10
events: list[Event] = [Event()] * count_of_threadings
threads: list[Thread] = [None] * count_of_threadings
counter = [0] * count_of_threadings

#старт | стоп | загрузка данных | вебсокет

def counter_threadings(index):
    while not events[index].is_set():
        counter[index] += 1
        time.sleep(1)

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.websocket("/ws/{id}")
async def websocket_endpoint(id: int, websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"total": sum(counter)})
            await asyncio.sleep(1)
    except:
        await websocket.close()

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

    return JSONResponse(content=messages)

@app.get("/stop/")
async def stop_threadings():
    for index in range(count_of_threadings):
        events[index].set()
    messages = {
        "messages": "Все потоки остановлены"
    }
    return JSONResponse(content=messages)

@app.get("/status/")
async def status_threadings():
    messages = {"counter": []}
    messages["counter"] = [{"id": index+1, "value": counter[index], "running": not events[index].is_set()} for index in range(count_of_threadings)]

    return JSONResponse(content=messages)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)