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
import exifread
import io
import re


def index(request):

    clear_media_folder()

    if  request.method == "POST":
        response = {}
        f = request.FILES['fileName'] # here you get the files needed
        # https://github.com/ianare/exif-py/blob/develop/exifread/classes.py
        tags = exifread.process_file(f,stop_tag='Image Orientation',details=False)
        orientation_value = tags.get('Image Orientation').values[0]
        response['transform'] = getTransform(orientation_value)
        # orientation = int(re.findall('\d+', orientation_string )[0])


        file_name = "pic.jpg"
        file_name_2 = default_storage.save(file_name, f)
        file_url = default_storage.url(file_name_2)

        numpy_image = cv.imread(file_url)
        response['img_url'] =  file_url
        solution, original_numbers = mySudokuSolver.solve_this(numpy_image)

        # response['solution'] = np.transpose(solution)
        #response['guessed'] =  np.transpose(original_numbers)
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

# https://exiftool.org/TagNames/EXIF.html
def getTransform(orientation_value):
    print(orientation_value)
    transform_dictionary = {1:'',\
                            2:'scaleX(-1)',\
                            3:'rotate(180deg)',\
                            4:'scaleY(-1)',\
                            5:'scaleY(-1) rotate(270deg)',\
                            6:'rotate(90deg)',\
                            7:'rotate(270deg)',\
                            8:'scaleY(-1) rotate(90deg)'}
    return transform_dictionary[orientation_value]
