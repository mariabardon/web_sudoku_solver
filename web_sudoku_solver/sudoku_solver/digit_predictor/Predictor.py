import torch
from .model import model
import cv2
import numpy as np
import torch.nn as nn
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

global predictor
def load_model(modelpath = 'digit_predictor/best_model.pth'):
    global predictor
    modelpath = os.path.join(BASE_DIR,modelpath)
    predictor = model.CNNet()
    predictor.load_state_dict(torch.load(modelpath, map_location='cpu'))
    for parameter in predictor.parameters():
        parameter.requres_grad = False
    predictor.eval()
    return

def getIMSIZE():
    return model.IMSIZE

def predict(imgs):
    imgs = np.expand_dims(imgs,1)
    if(np.max(imgs) > 1): imgs = imgs/255
    tensor_imgs = torch.tensor(np.array(imgs)).float()
    tensor_output = predictor(tensor_imgs)
    output = nn.functional.softmax(tensor_output,1)
    prediction = [np.argmax(output.detach().numpy())+1 for o in output]
    return(prediction)
