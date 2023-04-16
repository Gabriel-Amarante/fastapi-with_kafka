import os
import io as IO
import numpy as np
import csv
import json
import datetime
import dateparser
import dateutil.parser as dparser
from dateparser.search import search_dates

def identify_stage(dicio, obra_id):
  if (dicio[obra_id][0][6] == '1'):
    return "6"
  elif (dicio[obra_id][0][5] =='1'):
    return "5"
  elif (dicio[obra_id][0][4] == '1'):
    return "4"
  elif (dicio[obra_id][0][3] == '1'):
    return "3"
  elif (dicio[obra_id][0][2] == '1'):
    return "2"
  elif (dicio[obra_id][0][1] == '1'):
    return "1"
  else:
    return "0"

def identify_status(date_extracted, dateref):
    #dateref = datetime.datetime.today()
    if (date_extracted > dateref):
        return "Em dia"
    else:
        return "Atrasado"

def read_clause(path):
    with open(os.path.join(path, 'output.txt'), 'r') as f:
        lines = f.readlines()
    return str(lines[1].rstrip())

def clean_dates(found_dates, leave_out):
  lista = []
  for index, tuple in enumerate(found_dates):
        if tuple[0] in leave_out:
          continue
        lista.append(found_dates[index])
  return lista

def find_deadline(found_dates):
    novalista = []
    for index, tuple in enumerate(found_dates):
      novalista.append(tuple[1])
    if len(novalista) == 0:
        return None
    else:
        return max(novalista)

def main(path, dateref):
    with IO.open(os.path.join(path, 'predictions_final.csv'), "r", encoding="UTF-8") as file:
        data = np.genfromtxt(file, delimiter=",", dtype=None, encoding=None)

    dicio = {}
    for row in data[1:]:
      obra_id = row[0].rsplit('-', 1)[0]
      if(obra_id not in dicio):
        dicio[obra_id] = [row[2:]]
      else:
        dicio[obra_id] += [row[2:]]

    stage_dict = {
      "0": "Obra não iniciada(terreno)",
      "1": "Infra-estrutura",
      "2": "Vedacao vertical",
      "3": "Coberturas",
      "4": "Esquadrias",
      "5": "Revestimentos externos",
      "6": "Pisos externos e paisagismo",
    }

    current_stage = stage_dict[identify_stage(dicio, obra_id)]

    clause = read_clause(path)
    found_dates = (search_dates(clause, languages=['pt'], settings=None, add_detected_language=False, detect_languages_function=None))
    leave_out = ['segunda', 'quarta', 'quinta', 'sexta']
    if found_dates == None:
        deadline = None
    else:
        cleaned_dates = clean_dates(found_dates, leave_out)
        deadline = find_deadline(cleaned_dates)

    # identify status based on current stage and current date
    status = "Indeterminado"
    if (identify_stage(dicio, obra_id) == "6"):
        status = "Obra concluida"
    elif (deadline != None):
        status = identify_status(deadline, dateref)

    if deadline != None:
        deadline = deadline.strftime("%d/%m/%Y")

    my_dict = {'obra_id': obra_id, 'stage': current_stage, 'date_extracted': deadline, 'status': status, 'clause':clause}

    with open(os.path.join(path, 'data.json'), 'w') as fp:
        json.dump(my_dict, fp)
