import cv2 as cv
import numpy as np
import re
from .digit_predictor import Predictor as predictor
from .solver_files import ASP_interface
import sys

def pad_and_resize(digit,imsize):
    (w,h) = digit.shape
    w = int(h*2/3)
    digit = cv.resize(digit,(w,h))
    top_bottom_pad = h//7
    new_h = h + 2 * top_bottom_pad
    left_pad = (new_h-w)//2
    right_pad = new_h-(w+left_pad)
    digit = cv.copyMakeBorder(digit, top_bottom_pad , top_bottom_pad , left_pad, right_pad,\
                              borderType = cv.BORDER_CONSTANT, value=[0,0,0] )
    digit = cv.resize(digit,(imsize,imsize))
    return digit

def scaleImg(img):
    dim = (900,900)
    img = cv.resize(img, dim, interpolation = cv.INTER_AREA)
    return img

def find_cell(x_array, y_array ,c):
    [x,y] = c
    i = max([i for i,x_coor in enumerate(x_array) if x_coor < x])
    j = max([j for j,y_coor in enumerate(y_array) if y_coor < y])
    return i,j

def get_cells_centers(rows,columns):
    arr = []
    for i,r in enumerate(rows[:-1]):
        for j,c in enumerate(columns[:-1]):
            arr.append((rows[i] + (rows[i+1]-rows[i])//2,columns[j]+(columns[j+1]-columns[j])//2))
    return arr

def get_cell_center(r,c):
    x = rows[r] + (rows[r+1]-rows[r])//2
    y = columns[c] + (columns[c+1]-columns[c])//2
    return (x,y)

def get_contour_center(c):
    M = cv.moments(c)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    return(cX,cY)


def scan_image(img):
    img = scaleImg(img)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (5,5), 0)
    thresh = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2)
    my_contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)[-2:]
    # get contour with largest area (which is sudoku grid outside border),
    # approximate as polygonal shape
    largest_area = max([cv.contourArea(c) for c in my_contours])
    outside_contour = [c for c in my_contours if cv.contourArea(c) == largest_area][0]
    corners = cv.approxPolyDP(outside_contour,0.01*cv.arcLength(outside_contour,True),True)

    ############## from grid corners to new grid corners after perspective rectification
    corners=np.squeeze(corners)
    # naming indexes accoring to how the coordinates of the points related to the other points
    top_left_index = np.argmax([-sum(c) for c in corners])
    bottom_right_index = np.argmax([sum(c) for c in corners])
    bottom_left_index = np.argmax([c[1]-c[0] for c in corners])
    top_right_index = np.argmax([c[0]-c[1] for c in corners])

    min_x = min([c[0] for c in corners])
    min_y = min([c[1] for c in corners])
    max_x = max([c[0] for c in corners])
    max_y = max([c[1] for c in corners])

    index_to_new_corner = {top_left_index:[min_x,min_y],\
                           bottom_right_index:[max_x, max_y],\
                           top_right_index:[max_x,min_y],\
                           bottom_left_index:[min_x, max_y]}

    # cv.imshow(str(index_to_new_corner),thresh)
    # cv.waitKey(0)

    new_corners = np.array([index_to_new_corner[index] for index in range(len(corners))])
    ##############

    # find and apply homography to straighten the corners.
    h, status = cv.findHomography(corners, new_corners)
    new_perspective = cv.warpPerspective(img, h, img.shape[:2])

    cropped_img = scaleImg(new_perspective[min_y:max_y,min_x:max_x])

    grid_width = 900
    grid_height = 900
    grid_area = grid_width*grid_height
    rows = np.arange(0, 900, 100)
    columns = np.arange(0, 900, 100)

    #find and predict digits in the new image
    denoised = cv.fastNlMeansDenoisingColored(cropped_img,None,10,10,7,21)
    gray = cv.cvtColor(denoised, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (5,5), 0).astype('uint8')
    thresh2 = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 2)
    my_contours_cropped, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    # cv.imshow('thresh2',thresh2)
    # cv.waitKey(0)

    area_range = list(range(200,2700))
    height_range = list(range(30,90))
    width_range = list(range(15,60))
    # cv.imshow('thresh 2',thresh2)
    # cv.waitKey(0)

    mean = np.mean([cv.contourArea(c)  for c in my_contours_cropped if cv.contourArea(c) in area_range])
    d = mean.astype(int)//100
    thresh2 = cv.morphologyEx(thresh2, cv.MORPH_CLOSE, kernel=np.ones((d,d),np.uint8))
    my_contours_cropped, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    # cv.imshow('thresh last',thresh2)
    # cv.waitKey(0)

    predictor.load_model()
    sudoku_numbers = np.zeros((9,9), dtype=int)
    for cnt in my_contours_cropped:
        area = int(cv.contourArea(cnt))
        if area in area_range:
            [x,y,w,h] = cv.boundingRect(cnt)
            if h in height_range and w in width_range and 4>h/w>1.2:
                ctr = [x+w//2,y+h//2]
                i,j = find_cell(rows, columns ,ctr)
                digit = thresh2[y:y+h,x:x+w]
                digit = pad_and_resize(digit,predictor.getIMSIZE())
                predicted = predictor.predict([digit])
                sudoku_numbers[i][j] = str(predicted[0])
                # cv.imshow(str(predicted),digit)
                # cv.waitKey(0)
    return sudoku_numbers

def solve_sudoku(sudoku_numbers):
    asp_lines = []
    for i in range(9):
        for j in range(9):
            num = sudoku_numbers[i][j]
            if num != 0:
                asp_lines.append('value(cell({},{}),{}).'.format(i+1,j+1,int(sudoku_numbers[i][j])))
    solution_matrix = np.zeros((9,9), dtype=int)
    solution_matrix[sudoku_numbers!=0] = sudoku_numbers[sudoku_numbers!=0]


    try:
        solution = ASP_interface.solve(asp_lines)
    except RuntimeError as err:
        print('RuntimeError')
        print(err)
        solution = ''

    for e in solution:
        #i and j go from 0 to 8, but answer goes from 1 to 9
        [i,j,digit] = np.add( [int(c) for c in e if c.isdigit()] , [-1,-1,0] )
        solution_matrix[i][j]=digit

    # print(np.transpose(solution_matrix))
    return solution_matrix, sudoku_numbers


if __name__ == "__main__":
    img_name = 'sudoku_images/IMG-0997.JPG'    #+input('image name\n')
    img = cv.imread(img_name)
    solve_this(img)
