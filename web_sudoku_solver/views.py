from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import default_storage
from django.shortcuts import render
from .sudoku_solver import mySudokuSolver
from PIL import Image
from io import BytesIO
import sys, piexif, tempfile, uuid, os
import numpy as np
import cv2 as cv

def index(request):
    response = {}
    if  request.method == "POST":
        if 'solve' in request.POST:
            temp_url = request.POST['solve']
            numpy_image = cv.imread(temp_url)
            try:
                solution, original_numbers, numpy_cropped= mySudokuSolver.scan_image(numpy_image)
                s3_url, temp_url = save_image(Image.fromarray(numpy_cropped))
            except Exception as e:
                response['error'] = e
                save_image(Image.open(temp_url),error=True)
                return render(request,'web-sudoku-solver.html',response)

            z = zip(np.transpose(solution),np.transpose(original_numbers))
            response['temp_url'] =  temp_url
            response['original_numbers'] = np.dstack((np.transpose(solution),np.transpose(original_numbers)))
            response['solution'] =  solution
            response['s3_url'] = s3_url = temp_to_s3_name(temp_url)

        elif 'right' in request.POST:
            temp_url = request.POST['right']
            s3_url, temp_url = rotate_and_save(temp_url,-90)
            response['temp_url'] =  temp_url
            response['s3_url'] = s3_url
        elif 'left' in request.POST:
            temp_url = request.POST['left']
            s3_url, temp_url = rotate_and_save(temp_url,90)
            response['temp_url'] =  temp_url
            response['s3_url'] = s3_url
        else:
            origin_url = request.FILES['fileName'] # here you get the files needed
            s3_url, temp_url = rotate_with_exif_and_save(origin_url)

            try:
                s3_url, temp_url = rotate_with_exif_and_save(origin_url)

            except Exception as e:
                response['error'] = e
                save_image(Image.open(origin_url),error=True)
                return render(request,'web-sudoku-solver.html',response)
            response['temp_url'] =  temp_url
            response['s3_url'] = s3_url
        return render(request,'web-sudoku-solver.html',response)

    else:
        return render(request,'web-sudoku-solver.html')

def save_image(image, error=False):
    outputIoStream = BytesIO()
    outputIoStream.seek(0)
    w,h = image.size
    image = image.resize((500,500*h//w))
    try:
        image.save(outputIoStream , format='JPEG')
    except:
        image.save(outputIoStream , format='PNG')
    temp = tempfile.NamedTemporaryFile(delete=False)
    # unique_filename = str(uuid.uuid4())
    # s3_url = os.path.join('uploads',unique_filename+'.jpg')
    s3_url = temp_to_s3_name(temp.name)
    if error: s3_url = os.path.join('errors',s3_url)

    f = InMemoryUploadedFile(outputIoStream,'ImageField', 'image', 'image/jpeg',  sys.getsizeof(outputIoStream), None)

    with open(temp.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    default_storage.save(s3_url ,f)
    return s3_url, temp.name

def upload_as_error(image):
    outputIoStream = BytesIO()
    outputIoStream.seek(0)
    w,h = image.size
    image = image.resize((500,500*h//w))
    try:
        image.save(outputIoStream , format='JPEG')
    except:
        image.save(outputIoStream , format='PNG')
    unique_filename = str(uuid.uuid4())
    f = InMemoryUploadedFile(outputIoStream,'ImageField', s3_url, 'image/jpeg',  sys.getsizeof(outputIoStream), None)
    default_storage.save(os.path.join('errors',unique_filename+'.jpg'),f)


def temp_to_s3_name(temp_url):
    return temp_url.replace('/tmp/tmp','') + '.jpg'
# https://piexif.readthedocs.io/en/latest/sample.html
def rotate_with_exif_and_save(img_url):
    try:
        img = Image.open(img_url)
    except:
        raise Exception("Oops... This file is not an image. Please try again.")

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

def rotate_and_save(temp_url,d):
    img = Image.open(temp_url)
    img = img.rotate(d, expand=True)
    s3_url, temp_url = save_image(img)
    return s3_url, temp_url
