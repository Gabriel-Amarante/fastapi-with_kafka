import logging
import random
import brotli
import requests
import json
import shutil
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
        bootstrap_servers=get_settings().kafka_bootstrap_servers.split(','),
    )


app = create_application()
consumer = create_consumer()


async def decompress(file_bytes: bytes) -> str:
    return str(
        brotli.decompress(file_bytes),
        get_settings().file_encoding,
    )

def convertToJSON(predictions):
    # Separando as linhas do texto
    lines = predictions.strip().split('\n')

    # Obtendo os nomes das colunas a partir da primeira linha
    columns = lines[0].split(',')

    # Inicializando a lista para armazenar os registros
    records = []

    # Percorrendo as linhas de dados (exceto a primeira)
    for line in lines[1:]:
        values = line.split(',')
        record = dict(zip(columns, values))
        records.append(record)

    # Convertendo para JSON
    json_data = json.loads(json.dumps(records))

    return json_data

def findClasse(msg):
    classes = {
        "Outros": "0",
        "Obra nao iniciada (terreno)": "1",
        "Infra-estrutura": "2",
        "Vedacao vertical": "3",
        "Coberturas": "4",
        "Esquadrias": "5",
        "Revestimentos externos": "6",
        "Pisos externos e paisagismo": "7",    
    }

    for key, value in msg.items():
        if value == "1":
            return classes[key]
    return "0"
    

async def consume():
    while True:
        async for msg in consumer:
            id_urls = await decompress(msg.value)
            id_urls=id_urls.split(" ")
            id=id_urls[0]
            urls=id_urls[1:]
            responses=[]
            for url in urls:
                responses.append(requests.get(url))

            if os.path.exists("./app/obras"):
                os.chdir("./app/obras")

            if not os.path.exists("./images"):
                os.makedirs("./images")
            
            folder = "./images/"+str(random.randint(0,10000))
            if not os.path.exists(folder):
                os.makedirs(folder)

            for i in range(len(responses)):
                mypath = folder + "/to_predict_" + url[i][10:20] +".jpg"
                with open(mypath, "wb") as f:
                    f.write(responses[i].content)

            os.system("python3 Framework.py --path " + folder + "  --single_folder True")

            #retornar arquivo csv
            f = open(folder + "/" + "predictions.csv","r")
            classes = f.read()

            msg = convertToJSON(classes)
            #apagar pasta
            shutil.rmtree(folder)
            status = findClasse(msg[0])
            #enviar msg para backend
            try:
                os.getenv(BACKEND_URL)
                requests.patch(
                    #status deve ser a previsao
                    #id vai ser o da requisiçao 
                    os.getenv('BACKEND_URL')+'/collects/analytics/update/'+id+'?public_work_rnn_status='+status,
                    headers={"X-TRENA-KEY": os.getenv('API_KEY')},
                    verify=False,)
            except Exception as e:
                print("WARN:     Não atualizar o status do modelo para a coleta")


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
