import os
import io as IO
import numpy as np
import torch
import PIL
from PIL import Image
from sklearn import datasets
from skimage import io
from torch.utils.data import DataLoader
from torch.utils import data
import torch.nn as nn
import torchvision.transforms as T
import torchvision
import csv
import utils
from matplotlib import pyplot as plt
import torch.nn.functional as F
from joblib import dump, load
from sklearn.metrics import balanced_accuracy_score
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dataset_path', type=str, required=True)
parser.add_argument('--dest', type=str, required=True)
parser.add_argument('--target', type=int, required=True)
parser.add_argument('--class_name', type=str, required=True)
parser.add_argument('--threshold', type=int, required=True)
parser.add_argument('--threshold_target', type=int, required=True)
parser.add_argument('--num_epochs', type=int, required=True)
parser.add_argument('--lr', type=float, required=True)
parser.add_argument('--google', type=bool, default=False)
parser.add_argument('--pre_trained', type=bool, default=False)
args = parser.parse_args()

print("******STARTING " + args.class_name + "******")

def plotar(training_metrics, test_metrics):
    # Faz graficos
    # Transforming list into ndarray for plotting.
    training_array = np.asarray(training_metrics, dtype=np.float32)
    test_array = np.asarray(test_metrics, dtype=np.float32)

    # Plotting error metric.
    fig, ax = plt.subplots(1, 2, figsize = (16, 8), sharex=False, sharey=True)

    ax[0].plot(training_array)
    ax[0].set_xlabel('Training Loss Progression')

    ax[1].plot(test_array)
    ax[1].set_xlabel('Test Loss Progression')
    
    path = os.path.join(args.dest, "Charts/")
    if not os.path.isdir(path):
        os.mkdir(path)

    plt.savefig(os.path.join(path, args.class_name + ".png"))

class SIMECDataset(torch.utils.data.Dataset):
    def __init__(self, root, mode, transforms=None):
        self.root = root
        self.transforms = transforms
        self.mode = mode

        with IO.open(os.path.join(root, "labels_treino.csv"), "r", encoding="UTF-8") as file:
            self.data = np.genfromtxt(file, delimiter=",", dtype=None, encoding=None)

        self.imgs = np.array([])
        self.dicio = {}

        # Gera dicionario com info de cada imagem
        counter = np.array([0]*9)
        counter_target = 0

        for row in self.data[1:]:
            if(not int(row[1])):
                if((not int(row[args.target + 1])) and (np.min(counter[np.where(row == '1')]) > args.threshold)):
                    continue
                elif(int(row[args.target + 1]) and counter_target >= args.threshold_target and args.threshold_target > -1):
                    continue
                self.imgs = np.append(self.imgs, os.path.join(root, "IMAGES/" + row[0].split("-")[0] + "/" + row[0].split("-")[1] + ".jpeg"))
                k = row[0]
                v = row[1:]
                self.dicio[k] = v
                counter[np.where(row == '1')] += 1
                if(int(row[args.target + 1])):
                    counter_target += 1

        if(args.google):
            classes_name = ["terreno", "infraestrutura", "vedacao_vertical", "coberturas", "esquadrias", "revestimentos", "paisagismo"]

            for i, class_name in enumerate(classes_name):
                self.google_imgs = (sorted(os.listdir(os.path.join(root, "GIMAGES/" + class_name))))
                self.google_imgs = [os.path.join(root, "GIMAGES/" + class_name + "/" + s) for s in self.google_imgs]

                for s in self.google_imgs:
                    if(i == (args.target - 1) and args.threshold_target > -1 and counter_target >= args.threshold_target):
                        break
                    elif(i != (args.target - 1) and counter[i+2] >= args.threshold):
                        break

                    self.imgs = np.append(self.imgs, s)
                    id = s.split(".")[-2].split("/")
                    l = [0]*8
                    l[i+1] = 1
                    self.dicio[id[-2] + "-" + id[-1]] = l
                    if(i == (args.target - 1)):
                        counter_target += 1
                    elif(i != (args.target - 1)):
                        counter[i+2] += 1


        # Divide dataset em treino e teste
        np.random.seed(42)
        perm = np.random.permutation(len(self.imgs))

        if self.mode == "train":
            self.imgs = self.imgs[perm[:int(0.8 * perm.shape[0])]]
        elif self.mode == "test":
            self.imgs = self.imgs[perm[int(0.8 * perm.shape[0]):]]


    def __getitem__(self, idx):
        # Carrega image e label
        # img_path = os.path.join(self.root, self.imgs[idx])
        img_path = os.path.join('', self.imgs[idx])
        try:
            img = Image.open(img_path).convert("RGB")
        except:
            print(img_path)

        # Pega label do dicionario
        # print(self.imgs[idx])
        index = self.imgs[idx].split(".")[-2].split("/")
        # print(index)
        label = self.dicio[index[-2] + "-" + index[-1]][args.target]
        # print(img_path, label)

        # Transforma imagem em tensor
        if self.transforms is not None:
            img = self.transforms(img)

        label = int(label)
        return img, label

    def __len__(self):
        return len(self.imgs)


# Pega model de classificacao Resnet34
def get_classification_model():
    model = torchvision.models.resnet34(pretrained=args.pre_trained)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 2)
    return model


def get_transform(train):
    transforms = []
    if train:
        # during training, randomly flip the training images
        # and ground-truth for data augmentation
        transforms.append(T.RandomHorizontalFlip(0.5))

    # converts the image, a PIL image, into a PyTorch Tensor
    transforms.append(T.Resize((224, 224)))
    transforms.append(T.ToTensor())
    transforms.append(T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]))
    return T.Compose(transforms)


def set_dataset():
    # use our dataset and defined transformations
    dataset = SIMECDataset(root=args.dataset_path, mode="train", transforms=get_transform(train=True))
    dataset_test = SIMECDataset(root=args.dataset_path, mode="test", transforms=get_transform(train=False))

    # define training and validation data loaders
    data_loader = torch.utils.data.DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)
    data_loader_test = torch.utils.data.DataLoader(dataset_test, batch_size=1, shuffle=False, num_workers=4)

    # return (data_loader, data_loader_test)
    return data_loader, data_loader_test


def go(model, data_loader, data_loader_test):
    print(torch.cuda.is_available())
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

    num_classes = 2
    model.to(device)

    # print(model)

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss().to(device)
    # criterion = nn.CrossEntropyLoss(weight=torch.Tensor([0.06, 0.94])).to(device)

    training_metrics = list()
    test_metrics = list()

    labels = list()
    predictions = list()

    epochs = args.num_epochs
    for ep in range(epochs):
        labels = list()
        predictions = list()

        print('##############################################')
        print('Starting epoch ' + str(ep + 1) + '/' + str(epochs) + '...')

        # Setting model to training mode.
        print('    Training...')
        model.train()

        batch_metrics_train = np.array([])
        batch_metrics_test = np.array([])

        # Iterating over training batches.
        for it, data in enumerate(data_loader):
            # Obtaining data and labels for batch.
            inps, labs = data
            # GPU casting. In CPU version comment the following two lines.
            inps = inps.cuda()
            labs = labs.cuda()
            # Zeroing optimizer.
            optimizer.zero_grad()
            # Forwarding inps through NN.
            output = model(inps)
            # Computing loss according to network prediction for batch and targets.
            loss = criterion(output, labs)
            # Backpropagating loss.
            loss.backward() # All backward pass is computed from this line automatically by package torch.autograd.
            # Taking optimization step (updating NN weights).
            optimizer.step()
            # Appending metric for batch.
            batch_metrics_train = np.append(batch_metrics_train, loss.data.item())

        # Setting model to evaluation mode.
        training_metrics.append(np.mean(batch_metrics_train))
        print('    Testing...')
        model.eval()

        with torch.no_grad():
            label_list = list()
            output_list = list()

            # Iterating over test batches.
            for it, data in enumerate(data_loader_test):
                # Obtaining images and labels for batch.
                inps, labs = data
                # GPU casting. In CPU version comment the following line.
                inps = inps.cuda()
                labs = labs.cuda()
                # Forwarding inps through NN.
                output = model(inps)
                # Computing loss according to network prediction for batch and targets.
                loss = criterion(output, labs)
                # Appending metric for batch.
                batch_metrics_test = np.append(batch_metrics_test, loss.data.item())

                # Getting labels and predictions from last epoch.
                label_list += labs.cpu().numpy().tolist()
                output_list += output.max(1)[1].cpu().numpy().tolist()
                labels += labs.cpu().numpy().tolist()
                predictions += output.max(1)[1].cpu().numpy().tolist()

            test_metrics.append(np.mean(batch_metrics_test))

            label_array = np.asarray(label_list, dtype=np.int).ravel()
            output_array = np.asarray(output_list, dtype=np.int).ravel()

            print('Epoch: %d, Balanced Accuracy: %.2f%%' % (ep + 1, 100.0 * balanced_accuracy_score(label_array, output_array)))


    # Save stuff
    labels = np.asarray(labels, dtype=np.int).ravel()
    predictions = np.asarray(predictions, dtype=np.int).ravel()

    path1 = os.path.join(args.dest, "Labels e Predictions/")
    path2 = os.path.join(args.dest, "Redes Treinadas/")
    if not os.path.isdir(path1):
        os.mkdir(path1)
    if not os.path.isdir(path2):
        os.mkdir(path2)

    dump(labels, os.path.join(path1, "labels_" + args.class_name + ".joblib"))
    dump(predictions, os.path.join(path1, "predictions_" + args.class_name + ".joblib"))
    torch.save(model.state_dict(), os.path.join(path2, "Resnet34-" + args.class_name + ".pt"))
    
    plotar(training_metrics, test_metrics)


#################### MAIN #####################
model = get_classification_model()
data_loader, dataset = set_dataset()
go(model, data_loader, dataset)
