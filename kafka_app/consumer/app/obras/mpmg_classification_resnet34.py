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
parser.add_argument('--lr', type=float, required=False)
parser.add_argument('--lr_gamma', type=float, required=False)
parser.add_argument('--wd', type=float, required=False)
parser.add_argument('--version', type=str, required=False)
# Parse the argument
user_args = parser.parse_args()

# Setting predefined arguments.
args = {
    'epoch_num': 100,       # Number of epochs.
    'n_classes': 5,       # Number of classes.
    'lr': 1e-5,           # Learning rate.
    'weight_decay': 5e-3, # L2 penalty.
    'momentum': 0.9,      # Momentum.
    'num_workers': 4,     # Number of workers on data loader.
    'batch_size': 8,      # Mini-batch size.
    'w_size': 640,        # Width size for image resizing.
    'h_size': 640,        # Height size for image resizing.
    'lr_gamma': 0.92,
    'version':'test'
}

if torch.cuda.is_available():
    args['device'] = torch.device('cuda')
else:
    args['device'] = torch.device('cpu')

if user_args.lr is not None:
    args['lr'] = user_args.lr

if user_args.lr_gamma is not None:
    args['lr_gamma'] = user_args.lr_gamma

if user_args.wd is not None:
    args['weight_decay'] = user_args.wd

if user_args.version is not None:
    args['version'] = user_args.version

print('experiment version', args['version'], '- lr', args['lr'], '- device', args['device'], '- weight_decay', args['weight_decay'])


# Dataset and dataloader
path_to_dataset = "/mnt/DADOS_GRENOBLE_1/cristiano/mpmg/images"
path_to_data_file = "/mnt/DADOS_GRENOBLE_1/cristiano/mpmg/mpmg_annotations_final2.csv"

"""
Read image path and filenames from the dataset folders
"""



def parse_one_annot(annotations_data, filename):
    class_dict = {'Classe ':0, 'Classe 1':0, 'Classe 2':1, 'Classe 3':2, 'Classe 4':3, 'Classe 5':4}
    file_class = annotations_data[annotations_data["filename"] == filename]["label"].values.flatten()
    file_class = class_dict[file_class[0]]
    return file_class


all_images = [os.path.join(path_to_dataset, label, image)
                for label in os.listdir(path_to_dataset)
                  for image in os.listdir(os.path.join(path_to_dataset, label))]

annotations_data = pd.read_csv(path_to_data_file)
all_labels = []
for image in all_images:
  all_labels.append(parse_one_annot(annotations_data, image.split('/')[-1]))

X_train, X_test, y_train, y_test = train_test_split(all_images, all_labels, stratify=all_labels, test_size=0.20, random_state=42)
#print("We have {} samples, {} are training and {} testing".format(len(all_labels), len(y_train), len(y_test)))

class MPMGDataset(torch.utils.data.Dataset):
  def __init__(self, image_files, labels, transforms=None):
    self.image_files = image_files
    self.labels = labels
    self.transforms = transforms

  def __getitem__(self, idx):
    # load images and labels
    img = Image.open(self.image_files[idx]).convert("RGB")
    #label = torch.as_tensor(self.labels[idx], dtype=torch.int64)
    if self.transforms is not None:
      img = self.transforms(img)
    return img, self.labels[idx], (self.image_files[idx].split('/')[-2:])

  def __len__(self):
    return len(self.image_files)

# checking the dataset class
#dataset = MPMGDataset(X_train, y_train)
#dataset.__getitem__(20)

# Data Augmentation transforms.
data_transform = transforms.Compose([
    transforms.Resize((args['w_size'], args['h_size'])),
    transforms.RandomRotation(30),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# Setting datasets and dataloaders.
dataset_train = MPMGDataset(image_files = X_train,
                            labels = y_train,
                            transforms = data_transform)

dataset_test = MPMGDataset(image_files = X_test,
                           labels = y_test,
                           transforms = data_transform)

#for iters in range(1):
#    fig, ax = plt.subplots(1, 5, figsize=(20, 4))
#    for i, test_data in enumerate(dataset_test):
#        if i >= 5:
#            break
#        test_img, _ = test_data
#        ax[i].imshow(test_img.numpy().transpose(1, 2, 0))
#        ax[i].set_yticks([])
#        ax[i].set_xticks([])
#        ax[i].set_title('Image ' + str(i))
#    plt.show()

# define training and validation data loaders
train_loader = DataLoader(dataset_train,
                          batch_size = args['batch_size'],
                          num_workers=args['num_workers'],
                          shuffle=True)

test_loader = DataLoader(dataset_test,
                         batch_size = 1,
                         num_workers=args['num_workers'],
                         shuffle=False)

print("We have {} samples, {} are training and {} testing".format(len(all_labels), len(dataset_train), len(dataset_test)))


"""Network model and training
Defining the network, the optimizer and loss.
Creating the train and the test functions
"""

# Using predefined and pretrained model of ResNet18 on torchvision.
net = models.resnet34(pretrained=True).to(args['device'])
num_ftrs = net.fc.in_features
net.fc = nn.Linear(in_features=num_ftrs, out_features=args['n_classes'], bias=True).to(args['device'])

# Definindo o otimizador
optimizer = optim.Adam(net.parameters(),
                       lr=args['lr'],
                       betas=(args['momentum'], 0.999),
                       weight_decay=args['weight_decay'])

for state in optimizer.state.values():
    for k, v in state.items():
        if isinstance(v, torch.Tensor):
            state[k] = v.to(args['device'])

# Definindo a loss
class_weights = torch.FloatTensor([1.0, 3.74, 4.23, 2.02, 3.44]).cuda()
criterion = nn.CrossEntropyLoss(weight = class_weights).to(args['device'])
lr_scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=args['lr_gamma'])

# Funções para treino e teste
def train(train_loader, net, criterion, optimizer, epoch):

    tic = time.time()

    # Setting network for training mode.
    net.train()

    # Lists for losses and metrics.
    train_loss = []

    # Iterating over batches.
    for i, batch_data in enumerate(train_loader):
        # Obtaining images, labels and paths for batch.
        inps, labs, _ = batch_data

        # Casting to cuda variables.
        inps = inps.to(args['device'])
        labs = labs.to(args['device'])
        labs = torch.flatten(labs)

        # Clears the gradients of optimizer.
        optimizer.zero_grad()

        # Forwarding.
        outs = net(inps)

        # Computing loss.
        loss = criterion(outs, labs)

        # Computing backpropagation.
        loss.backward()
        optimizer.step()

        # Updating lists.
        train_loss.append(loss.data.item())

    toc = time.time()
    train_loss = np.asarray(train_loss)
    writer.add_scalar("train/loss", train_loss.mean(), epoch)

    # Printing training epoch loss and metrics.
    print('--------------------------------------------------------------------')
    print('[epoch %d], [train loss %.4f +/- %.4f], [training time %.2f]' % (
        epoch, train_loss.mean(), train_loss.std(), (toc - tic)))
    print('--------------------------------------------------------------------')

def test(test_loader, net, criterion, epoch, last):

    tic = time.time()

    # Setting network for evaluation mode (not computing gradients).
    net.eval()

    # Lists for losses and metrics.
    test_loss = []
    prd_list = []
    lab_list = []
    fails_list = []

    # Iterating over batches.
    for i, batch_data in enumerate(test_loader):

        # Obtaining images, labels and paths for batch.
        inps, labs, image_name = batch_data

        # Casting to cuda variables.
        inps = inps.to(args['device'])
        labs = labs.to(args['device'])
        labs = torch.flatten(labs)

        # Forwarding.
        outs = net(inps)

        # Computing loss.
        loss = criterion(outs, labs)

        # Obtaining predictions.
        prds = outs.data.max(dim=1)[1].cpu().numpy()

        # Obtaining samples wrongly classified in the last epoch
        if labs.cpu().numpy() != prds:
            image_name = (list(image_name))
            fails_list.append((prds, labs.cpu().numpy()[0], image_name))

        # Updating lists.
        test_loss.append(loss.data.item())
        prd_list.append(prds)
        lab_list.append(labs.detach().cpu().numpy())

    toc = time.time()

    # Computing accuracy.
    acc = metrics.accuracy_score(np.asarray(lab_list).ravel(),
                                 np.asarray(prd_list).ravel())

    balanced_acc = metrics.balanced_accuracy_score(np.asarray(lab_list).ravel(),
                                                   np.asarray(prd_list).ravel())

    test_loss = np.asarray(test_loss)

    if last == True:
        # compute cm
        cm = metrics.confusion_matrix(np.asarray(lab_list).ravel(), np.asarray(prd_list).ravel())
        disp = metrics.ConfusionMatrixDisplay(cm , display_labels=("1","2","3","4","5"))
        disp.plot()
        plt.savefig('cmatrix/confusionmatrix'+args['version']+'.png')

        f = open('fails_list_'+args['version']+'.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)
        w.writerow(('prediction', 'true_label', 'image_file'))
        for element in fails_list:
            w.writerow(element)

    writer.add_scalar("test/acc", acc, epoch)
    writer.add_scalar("test/balanced_acc", balanced_acc, epoch)
    writer.add_scalar("test/loss", test_loss.mean(), epoch)

    # Printing training epoch loss and metrics.
    print('--------------------------------------------------------------------')
    print('[epoch %d], [test loss %.4f +/- %.4f], [acc %.4f], [balanced_acc %.4f], [testing time %.2f]' % (
        epoch, test_loss.mean(), test_loss.std(), acc, balanced_acc, (toc - tic)))
    print('--------------------------------------------------------------------')

"""# Training procedure"""

writer = SummaryWriter(comment=args['version'])
# Iterating over epochs.
for epoch in range(1, args['epoch_num'] + 1):

    last = False
    if epoch == args['epoch_num']:
        last = True

    # Training function.
    train(train_loader, net, criterion, optimizer, epoch)

    # Computing test loss and metrics.
    test(test_loader, net, criterion, epoch, last)

    lr_scheduler.step()
    print("current lr:", lr_scheduler.get_last_lr())

writer.close()
