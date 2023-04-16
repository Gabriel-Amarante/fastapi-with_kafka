Para baixar as imagens do streetview

1. Gerar coordenadas geográficas das imagens a serem obtidas:

Criar um arquivo .csv com todos os nomes das regiões/cidades, a quantidade de coordenadas a serem geradas por região e as respectivas coordenadas delimitadores da região. A região deve ser delimitada com
um quadrilátero. Conforme segue:

@region,@samples,@lat_min,@lon_min,@lat_max,@lon_max
rmbh,200,-20.035844,-44.224533,-19.582630,-43.887425

Executar o script street_view_coordinates que irá gerar as coordenadas aleatórias
dentro da area delimitada e criar um arquivo .csv para cada região/cidade.

2. Fazer o download das imagens

O script download_data pega as imagens para um arquivo .csv de cada vez.
O script download_all executa o download_data para cada cidade/região (arquivo .csv)

No script download_data tem que incluir a Key do usuário para Google Streetview