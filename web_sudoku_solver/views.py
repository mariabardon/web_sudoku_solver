from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import numpy as np
import cv2 as cv
from django.http import HttpResponse
from .sudoku_solver import mySudokuSolver
#from . import mySudokuSolver
# Create your views here.

def index(request):
#    return HttpResponse("<em>Hello World!</em>")


    if  request.method == "POST":
        f = request.FILES['sentFile'] # here you get the files needed
        response = {}
        file_name = "pic.jpg"
        file_name_2 = default_storage.save(file_name, f)
        file_url = default_storage.url(file_name_2)

        numpy_image = cv.imread(file_url)
        numbers = mySudokuSolver.solve_this(numpy_image)

        response['name'] = settings.BASE_DIR+'/'+file_url
        default_storage.delete(file_name)

        return render(request,'homepage.html',response)
    else:
        return render(request,'homepage.html')
