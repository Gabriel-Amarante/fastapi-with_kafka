import pycurl
import scrapy
import csv
import os
from datetime import datetime
from scrapy.http.request import Request

now = datetime.now()
dt_string = now.strftime("%Y-%m-%d_%Hh%Mm")
path = "IMAGES_" + dt_string;
	
if not os.path.exists(path):
    os.mkdir(path)

with open(path + '/general_data.csv', 'w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',')
    spamwriter.writerow(["ID", "Título","Situação","Município - UF","Localização","CEP","Endereço","Bairro","Termo/Convênio","Fim da Vigência","Situação do Termo","Data da Última Vistoria","Percentual de Execução"])

class SIMECSpider(scrapy.Spider):
    name = "simec_spider"

    def start_requests(self):
        if(not hasattr(self, "max_id")):
            self.max_id = 40000
        start_urls = [f'http://simec.mec.gov.br/painelObras/vistoria.php?obra={i}' for i in range(8062, int(self.max_id))]
        for url in start_urls:
            yield Request(url, self.parse)

    def parse(self, response):
        id = response.url.split("=")[1]

        title = response.xpath(".//h2/text()").get() #Titulo
        if title == None:
            print("None")
            return

        attr = response.xpath(".//dd/text()").getall() #Situacao
        if len(attr) < 10:
            print("Attr")
            return

        data = [
            id, #ID
            response.xpath(".//h2/text()").get(), #Titulo
            response.xpath(".//dd/span/text()").getall()[0][60:], #Situacao
            response.xpath(".//dd/text()").getall()[0], #Municipio - UF
            response.xpath(".//dd/a").css("::attr(coord)").get(), #Coordenadas
            response.xpath(".//dd/text()").getall()[1], #CEP
            response.xpath(".//dd/text()").getall()[2], #Endereco
            response.xpath(".//dd/text()").getall()[3], #Bairro
            response.xpath(".//dd/text()").getall()[4], #Termo/Convenio
            response.xpath(".//dd/text()").getall()[5], #Fim da Vigencia
            response.xpath(".//dd/text()").getall()[6], #Situacao do Termo
            response.xpath(".//dd/text()").getall()[7], #Data da Ultima Vistoria
            response.xpath(".//dd/text()").getall()[9] #Percentual de Execucao
        ]
        images = response.xpath(".//a").css(".img_foto::attr(src)").getall()

        with open(path + '/general_data.csv', 'a', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow(data)

        if not os.path.exists(path + "/" + id):
            os.mkdir(path + "/" + id)

        for i, img in enumerate(images):
            file = open(f"{path}/{id}/{i}.jpeg", "wb")
            crl = pycurl.Curl()
            crl.setopt(crl.URL, img)
            crl.setopt(crl.WRITEDATA, file)
            crl.perform()
            crl.close()
            file.close()
