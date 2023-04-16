import os
import io as IO
import numpy as np
import csv

def main(path, threshold):
	with IO.open(os.path.join(path, 'predictions.csv'), "r", encoding="UTF-8") as file:
		data = np.genfromtxt(file, delimiter=",", dtype=None, encoding=None)


	dicio = {}
	for row in data[1:]:
		obra_id = row[0].rsplit('-', 1)[0]
		if(obra_id not in dicio):
			dicio[obra_id] = [row[3:]]
		else:
			dicio[obra_id] += [row[3:]]


	obra_predictions = {}
	for k, v in dicio.items():
		labels = [0,0,0,0,0,0,0]
		for image in v:
			for i in range(0, 14, 2):
				print(image)
				if(image[i] == '1' and float(image[i+1]) >= threshold):
					labels[int(i/2)] += 1

		obra_predictions[k] = labels


	final_obra_predictions = {}
	class_names = ["terreno", "infraestrutura", "vedacao_vertical", "coberturas", "esquadrias", "revestimentos", "paisagismo"]
	for k, v in obra_predictions.items():
		final = [0,0,0,0,0,0,0]
		aux = np.copy(v)
		aux[3] = aux[4] = 0

		if(np.max(aux) > 0):
			base_label = np.where(aux == np.max(aux))[0][-1]
			final[base_label] = 1

		if(final[5] or final[6]):
			final[4] = int(v[4] > 0)

		if(final[2] or final[5] or final[6]):
			final[3] = int(v[3] > 0)

		final_obra_predictions[k] = final


	with open(os.path.join(path, 'predictions_final.csv'), 'w', newline='') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',')
			spamwriter.writerow(["ID","Outros","Obra nao iniciada (terreno)","Infra-estrutura",
			"Vedacao vertical","Coberturas","Esquadrias","Revestimentos externos","Pisos externos e paisagismo"])

			for k, v in final_obra_predictions.items():
				if(np.sum(v) == 0):
					line = [k,1]
				else:
					line = [k,0]
				for i in range(7):
					line += [int(v[i])]
				spamwriter.writerow(line)
