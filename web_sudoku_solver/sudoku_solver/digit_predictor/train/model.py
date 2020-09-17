import torch.nn as nn
import torch.nn.functional as F
## This model gets images as arrays of one dimension of length IMSIZE*IMSIZE
# it classifies 9 different classes.
global IMSIZE
IMSIZE = 56
class CNNet(nn.Module):
    def __init__(self):
        super(CNNet, self).__init__()
        # input IMSIZE x IMSIZE x 1
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        # input IMSIZE x IMSIZE x 32
        self.conv2 = nn.Conv2d(32, 32, 3, padding=1)
        # input IMSIZE/2 x IMSIZE/2 x 32
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        # input IMSIZE/2 x IMSIZE/2 x 64
        self.conv4 = nn.Conv2d(64, 64, 3, padding=1)

        # input IMSIZE/4 x IMSIZE/4 x 64

        self.fc1 = nn.Linear((IMSIZE**2)*4, 1024)
        self.fc2 = nn.Linear(1024, 9)

        self.maxpool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = self.maxpool(x)
        x = F.relu(self.conv3(x))
        x = F.relu(self.conv4(x))
        x = self.maxpool(x)

        x = x.view(-1,(IMSIZE**2)*4)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x
