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
import io
import re
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import piexif
global file_url
file_url = os.path.join(settings.BASE_DIR,'static','media','pic.jpg')

def index(request):
    global file_url
    response = {}
    if  request.method == "POST":
        if 'solve' in request.POST:
            numpy_image = cv.imread(file_url)
            original_numbers = mySudokuSolver.scan_image(numpy_image)
            solution = mySudokuSolver.solve_sudoku(original_numbers)
            z = zip(np.transpose(solution),np.transpose(original_numbers))
            response['img_url'] =  file_url
            response['original_numbers'] = np.dstack((np.transpose(solution),np.transpose(original_numbers)))
            response['solution'] =  solution
        elif 'right' in request.POST:
            file_url = rotate_and_save(file_url,-90)
            response['img_url'] =  file_url
        elif 'left' in request.POST:
            file_url = rotate_and_save(file_url,90)
            response['img_url'] =  file_url
        else:
            clear_media_folder()
            f = request.FILES['fileName'] # here you get the files needed
            file_url = rotate_with_exif_and_save(f)
            response['img_url'] =  file_url

        return render(request,'homepage.html',response)

    else:
        return render(request,'homepage.html')

def clear_media_folder():
    folder = os.path.join(settings.BASE_DIR,'static','media')
    for filename in [f for f in os.listdir(folder) if 'my_logo' not in f]:
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    folder= os.path.join(settings.BASE_DIR,'staticfiles','media')
    for filename in [f for f in os.listdir(folder) if 'my_logo' not in f]:
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def save_image(image):
    file_name = "pic.jpg"
    outputIoStream = BytesIO()
    outputIoStream.seek(0)
    w,h = image.size
    image = image.resize((500,500*h//w))
    try:
        image.save(outputIoStream , format='JPEG')
    except:
        image.save(outputIoStream, format='png')
    f = InMemoryUploadedFile(outputIoStream,'ImageField', file_name, 'image/jpeg',  sys.getsizeof(outputIoStream), None)
    clear_media_folder()
    file_name_2 = default_storage.save(file_name, f)
    file_url = default_storage.url(file_name_2)
    return file_url

# https://piexif.readthedocs.io/en/latest/sample.html
def rotate_with_exif_and_save(filename):
    img = Image.open(filename)
    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
        if piexif.ImageIFD.Orientation in exif_dict["0th"]:
            orientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
            exif_bytes = piexif.dump(exif_dict)
            if orientation == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                img = img.rotate(180)
            elif orientation == 4:
                img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 5:
                img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 6:
                img = img.rotate(-90, expand=True)
            elif orientation == 7:
                img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    return save_image(img)


def rotate_and_save(file_url,d):
    img = Image.open(file_url)
    img = img.rotate(d, expand=True)
    file_url = save_image(img)
    return file_url
