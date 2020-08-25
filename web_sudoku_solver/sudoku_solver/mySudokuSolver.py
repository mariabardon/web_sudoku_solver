import cv2 as cv
import numpy as np
import re
#import digit_predictor.Predictor as predictor
#import solver_files.ASP_interface as ASP_interface
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
    dim = (960,960)
    img = cv.resize(img, dim, interpolation = cv.INTER_AREA)
    return img

def find_cell(x_array, y_array ,x,y):
    i = max([i for i,x_coor in enumerate(x_array) if x_coor < x])
    j = max([j for j,y_coor in enumerate(y_array) if y_coor < y])
    return i,j


def test(img):
    return 'yes'

def turn_image(img):
    img=cv.transpose(img)
    img=cv.flip(img,flipCode=1)
    return img

def scan_image(img):
    img = scaleImg(img)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (5,5), 0)
    thresh = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)[-2:]
    # get contour with largest area (which is sudoku grid outside border),
    # approximate as polygonal shape, and mask the image with the aproximated contour.
    largest_area = max([cv.contourArea(c) for c in contours])
    outside_contour = [c for c in contours if cv.contourArea(c) == largest_area][0]
    mask = np.zeros((img.shape),np.uint8)
    corners = cv.approxPolyDP(outside_contour,0.01*cv.arcLength(outside_contour,True),True)

    cv.drawContours(mask,[corners],0,(255,255,255),-1)
    sudoku_masked = np.zeros_like(img)
    sudoku_masked[mask==255] = img[mask==255]
    # cv.imshow('sudoku_masked', sudoku_masked)
    # cv.waitKey(0)

    ############## from grid corners to new grid corners after perspective rectification
    corners=np.squeeze(corners)
    # naming indexes accoring to how the coordinates of the points related to the other points
    top_left_index = np.argmax([-sum(c) for c in corners])
    bottom_right_index = np.argmax([sum(c) for c in corners])
    bottom_left_index = np.argmax([c[1]-c[0] for c in corners])
    top_right_index = np.argmax([c[0]-c[1] for c in corners])

    a = 5
    min_x = min([c[0] for c in corners])+a
    min_y = min([c[1] for c in corners])+a
    max_x = max([c[0] for c in corners])-a
    max_y = max([c[1] for c in corners])-a

    index_to_new_corner = {top_left_index:[min_x,min_y],\
                           bottom_right_index:[max_x, max_y],\
                           top_right_index:[max_x,min_y],\
                           bottom_left_index:[min_x, max_y]}

    new_corners = np.array([index_to_new_corner[index] for index in range(len(corners))])
    ##############

    # create and apply homography, with current and new corners, to the required image
    h, status = cv.findHomography(corners, new_corners)
    new_perspective = cv.warpPerspective(img, h, img.shape[:2])
    new_sudoku_masked = new_perspective[min_y:max_y,min_x:max_x]

    grid_width = max_x - min_x
    grid_height = max_y - min_y
    rows = np.arange(min_x, max_x, grid_width//9)
    columns = np.arange(min_y, max_y, grid_height//9)
    grid_area = grid_width*grid_height

    rows = np.arange(0, grid_width, grid_width//9)
    columns = np.arange(0, grid_height, grid_height//9)


    #find and predict digits in the new image
    denoised = cv.fastNlMeansDenoisingColored(new_sudoku_masked,None,10,10,7,21)
    gray = cv.cvtColor(denoised, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (5,5), 0).astype('uint8')
    thresh2 = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    cv.imshow('new_threshold', thresh2)
    cv.waitKey(0)

    max_area = grid_area//360
    min_area = grid_area//9000
    max_height = grid_height//12
    min_height = grid_height//30

    #print(grid_area,min_area,max_area)
    #print(grid_height,min_height,max_height)
    predictor.load_model()
    imsize = predictor.getIMSIZE()

    sudoku_numbers = np.zeros((9,9), dtype=int)
    # asp_lines = []
    for cnt in contours:
        area = cv.contourArea(cnt)
        if max_area > area and area > min_area:
            [x,y,w,h] = cv.boundingRect(cnt)
            if max_height > h and h > min_height:
                digit = thresh2[y:y+h,x:x+w]
                digit = pad_and_resize(digit,imsize)
                predicted = predictor.predict([digit])
                #print('predicted', predicted[0])
                # cv.imshow('digit', digit)
                # cv.waitKey(0)
                i,j = find_cell(rows, columns ,x,y)
                sudoku_numbers[i][j] = str(predicted[0])
                # print(predicted[0],'at:',i,j)
                # asp_lines.append('value(cell({},{}),{}).'.format(i+1,j+1,predicted[0]))
    return sudoku_numbers

def solve_sudoku(sudoku_numbers):
    # print(sudoku_numbers)
    asp_lines = []
    for i in range(9):
        for j in range(9):
            num = sudoku_numbers[i][j]
            if num != 0:
                asp_lines.append('value(cell({},{}),{}).'.format(i+1,j+1,int(sudoku_numbers[i][j])))
    # print(asp_lines)
    solution_matrix = np.zeros((9,9), dtype=int)
    solution_matrix[sudoku_numbers!=0] = sudoku_numbers[sudoku_numbers!=0]

    solution = ASP_interface.solve(asp_lines)
    for e in solution:
        #i and j go from 0 to 8, but answer goes from 1 to 9
        [i,j,digit] = np.add( [int(c) for c in e if c.isdigit()] , [-1,-1,0] )
        solution_matrix[i][j]=digit

    # print(np.transpose(solution_matrix))
    return solution_matrix, sudoku_numbers


if __name__ == "__main__":
    #img_name = 'sudoku_images/su.jpg'    #+input('image name\n')
    #img_name = 'sudoku_images/1113.png'    #+input('image name\n')
    #img_name = 'sudoku_images/1114.JPG'    #+input('image name\n')
    #img_name = 'sudoku_images/IMG-0996.JPG'    #+input('image name\n')
    img_name = 'sudoku_images/IMG-0997.JPG'    #+input('image name\n')
    #img_name = 'sudoku_images/IMG-0998.JPG'    #+input('image name\n')
    #img_name = 'sudoku_images/IMG-0999.JPG'    #+input('image name\n')
    #img_name = 'sudoku_images/IMG-1001.JPG'    #+input('image name\n')
    #img_name = 'sudoku_images/IMG-1002.JPG'    #+input('image name\n')
    #img_name = 'sudoku_images/IMG-1003.JPG'    #+input('image name\n')
    img = cv.imread(img_name)
    solve_this(img)
