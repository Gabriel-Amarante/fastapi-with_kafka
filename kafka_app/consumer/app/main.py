import logging
import random
import brotli
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI

from app.config import get_settings

import requests
import os

log = logging.getLogger("uvicorn")


def create_application() -> FastAPI:
    """Create FastAPI application and set routes.
    Returns:
        FastAPI: The created FastAPI instance.
    """

    return FastAPI()


def create_consumer() -> AIOKafkaConsumer:

    return AIOKafkaConsumer(
        get_settings().kafka_topics,
        bootstrap_servers=get_settings().kafka_instance,
    )


app = create_application()
consumer = create_consumer()


async def decompress(file_bytes: bytes) -> str:
    return str(
        brotli.decompress(file_bytes),
        get_settings().file_encoding,
    )


async def consume():
    while True:
        async for msg in consumer:
            image_url = await decompress(msg.value)

            os.chdir("./app/obras")

            if not os.path.exists("./images"):
                os.makedirs("./images")
            
            response = requests.get(image_url)
            folder = "./images/"+str(random.randint(0,10000))
            if not os.path.exists(folder):
                os.makedirs(folder)

            mypath = folder + "/to_predict_"+image_url[10:20]+".jpg"
            with open(mypath, "wb") as f:
                f.write(response.content)

            os.system("python3 Framework.py --path " + folder + "  --single_folder True")

            #retornar arquivo csv
            f = open(folder + "/" + "predictions.csv","r")
            classes = f.read()

            #shutil.rmtree(folder)
            print(classes)
            msg = classes



@app.on_event("startup")
async def startup_event():
    """Start up event for FastAPI application."""

    log.info("Starting up...")
    await consumer.start()
    await consume()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for FastAPI application."""

    log.info("Shutting down...")
    await consumer.stop()
