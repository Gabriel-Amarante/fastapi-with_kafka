# -*- coding: utf-8 -*-
"""
Classification task of images of the mpmg dataset containing
images of paved streets and non paved streed

Basic imports and setting pre-defined arguments
"""

import os
import time
import numpy as np
import pandas as pd
import torch
import argparse
import csv

from torch import nn
from torch import optim

from torch.utils.data import DataLoader
from torch.utils import data
from torch.backends import cudnn

from torchvision import models
from torchvision import datasets
from torchvision import transforms
from torch.utils.tensorboard import SummaryWriter

from PIL import Image

from skimage import io

from sklearn import metrics
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from matplotlib import pyplot as plt

# benchmark mode is good whenever your input sizes for your network do not vary
# But if your input sizes changes at each iteration, then cudnn will benchmark
# every time a new size appears, possibly leading to worse runtime performances.
cudnn.benchmark = True

# Create the parser
parser = argparse.ArgumentParser()
# Add an argument
parser.add_argument('--path', type=str, required=True)

# Parse the argument
user_args = parser.parse_args()

# Setting predefined arguments.
args = {
    'n_classes': 5,       # Number of classes.
    'num_workers': 4,     # Number of workers on data loader.
    'batch_size': 1,      # Mini-batch size.
    'w_size': 640,        # Width size for image resizing.
    'h_size': 640,        # Height size for image resizing.
    }

if torch.cuda.is_available():
    args['device'] = torch.device('cuda')
else:
    args['device'] = torch.device('cpu')

if user_args.path is not None:
    path_to_dataset = user_args.path

"""
Read image path and filenames from the dataset folders
"""

all_images = [os.path.join(path_to_dataset, image)
                  for image in os.listdir(path_to_dataset)]

class MPMGDataset(torch.utils.data.Dataset):
  def __init__(self, image_files, transforms=None):
    self.image_files = image_files
    self.transforms = transforms

  def __getitem__(self, idx):
    # load images
    img = Image.open(self.image_files[idx]).convert("RGB")
    if self.transforms is not None:
      img = self.transforms(img)
    return img, (self.image_files[idx].split('/')[-2:])

  def __len__(self):
    return len(self.image_files)

# Data Augmentation transforms.
data_transform = transforms.Compose([
    transforms.Resize((args['w_size'], args['h_size'])),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Setting datasets and dataloaders.
dataset_test = MPMGDataset(image_files = all_images,
                           transforms = data_transform)

# define training and validation data loaders
test_loader = DataLoader(dataset_test,
                         batch_size = args['batch_size'],
                         num_workers=args['num_workers'],
                         shuffle=False)

"""Network model and training
Defining the network, the optimizer and loss.
Creating the train and the test functions
"""

# Using predefined and pretrained model of ResNet18 on torchvision.
net = models.resnet34(pretrained=True).to(args['device'])
num_ftrs = net.fc.in_features
net.fc = nn.Linear(in_features=num_ftrs, out_features=args['n_classes'], bias=True).to(args['device'])

# use models from folder "networks", used in API
if not os.path.isdir("model.pth"):
    net.load_state_dict(torch.load("./networks/model_pavimentacao_resnet34.pth"))
else:
    net.load_state_dict(torch.load("model.pth"))



def test(test_loader, net):

    tic = time.time()

    # Setting network for evaluation mode (not computing gradients).
    net.eval()

    # Lists for losses and metrics.
    prd_list = []

    # Iterating over batches.
    for i, batch_data in enumerate(test_loader):

        # Obtaining images and paths for batch.
        inps, image_name = batch_data

        # Casting to cuda variables.
        inps = inps.to(args['device'])

        # Forwarding.
        outs = net(inps)

        # Obtaining predictions.
        prds = outs.data.max(dim=1)[1].cpu().numpy()

        class_dict = {0:1, 1:2, 2:3, 3:4, 4:5}
        class_name = {0:"Pavimentado", 1:"Não pavimentado", 2:"Pavimentação alternativa", 3:"Semi-pavimentado", 4:"Em pavimentação"}
        prds_numbered = class_dict[prds.item(0)]
        prds_named = class_name[prds.item(0)]

        image_name = np.asarray(image_name)

        # Updating lists.
        prd_list.append((image_name.item(-1), prds_numbered, prds_named))

        toc = time.time()

        # create a list containing the classifications
        f = open('classification_list.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)
        w.writerow(('image_name', 'classification', 'classe_name'))
        for element in prd_list:
            w.writerow(element)


# Computing forward
test(test_loader, net)
print("\nCheck classification_list.csv file to see the predictions.\n")
