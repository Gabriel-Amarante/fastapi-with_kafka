import logging

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

            response = requests.get(image_url)
            if not os.path.exists("./images"):
                os.makedirs("./images")

            mypath = "./images/to_predict_"+image_url[10:20]+".jpg"
            with open(mypath, "wb") as f:
                f.write(response.content)

            print(os.listdir("./images/"))

            os.system("pwd")
            print(os.listdir())

            os.chdir("app/obras")

            os.system("python3 Framework.py --path " + mypath + "  --single_folder True")

#            #retornar arquivo csv
            f = open(mypath + "predictions.csv","r")
            classes = f.read()
#            f1 = open(mypath + "predictions_final.csv","r")
#            details = f1.read()
#
#            #remover pasta com dados anteriores
#            shutil.rmtree(mypath)
#
#            #voltar diretorio padrão e retornar predições
#
#            print(os.listdir("./images/"))
#
            msg = classes

#            msg = "Classe 1"


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

