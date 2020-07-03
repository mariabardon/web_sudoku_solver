import os, shutil
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

    clear_media_folder()
    if  request.method == "POST":
        f = request.FILES['chosenFile'] # here you get the files needed
        response = {}
        file_name = "pic.jpg"
        file_name_2 = default_storage.save(file_name, f)
        file_url = default_storage.url(file_name_2)

        numpy_image = cv.imread(file_url)

        print('This is the file_url ',file_url)

        numbers = mySudokuSolver.solve_this(numpy_image)
        
        response['name'] = np.transpose(numbers)

        return render(request,'homepage.html',response)
    else:
        return render(request,'homepage.html')

def clear_media_folder():
    folder = os.path.join(settings.BASE_DIR,'static','media')
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
