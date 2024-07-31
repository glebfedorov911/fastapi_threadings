from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from threading import Event, Thread

import uvicorn
import time
import asyncio


app = FastAPI()
templates = Jinja2Templates(directory="templates")
count_of_threadings = 10
threads: list[Thread] = [None] * count_of_threadings
counter = [0] * count_of_threadings

user_data = {}

#старт | стоп | загрузка данных | вебсокет

def counter_threadings(index, user_id):
    global user_data
    while not user_data[user_id]["events"][index].is_set():
        user_data[user_id]["counter"][index] += 1
        time.sleep(1)

@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.websocket("/ws/{us_id}")
async def websocket_endpoint(us_id: int, websocket: WebSocket, response: Response):
    global user_data
    
    user_data[us_id] = {"events": [Event() for _ in range(count_of_threadings)], "threads": threads.copy(), "counter": counter.copy()}
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"total": sum(user_data[us_id]["counter"])})
            await asyncio.sleep(1)
    except:
        await websocket.close()

@app.get("/start/")
async def start_threadings(user_id: int | None = Cookie(default=None)):
    global user_data
    messages = []
    for index in range(count_of_threadings):
        if user_data[user_id]["threads"][index] is None or not user_data[user_id]["threads"][index].is_alive():
            user_data[user_id]["events"][index].clear()
            user_data[user_id]["threads"][index] = Thread(target=counter_threadings, args=(index, user_id))
            user_data[user_id]["threads"][index].start()
            messages.append(f"Счетчик {index+1} стартовал")
        else:
            messages.append(f"Счетчик {index+1} уже запущен")

    return JSONResponse(content=messages)

@app.get("/stop/")
async def stop_threadings(user_id: int | None = Cookie(default=None)):
    global user_data
    for index in range(count_of_threadings):
        user_data[user_id]["events"][index].set()
    messages = {
        "messages": "Все потоки остановлены"
    }
    return JSONResponse(content=messages)

@app.get("/status/")
async def status_threadings(user_id: int | None = Cookie(default=None)):
    global user_data
    messages = {"counter": []}
    messages["counter"] = [{"id": index+1, "value": user_data[user_id]["counter"][index], "running": not user_data[user_id]["events"][index].is_set()} for index in range(count_of_threadings)]

    return JSONResponse(content=messages)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)