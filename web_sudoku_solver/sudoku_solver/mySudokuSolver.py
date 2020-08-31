import cv2 as cv
import numpy as np
import re
from imutils import contours
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

def get_cells_centers(rows,columns):
    arr = []
    for i,r in enumerate(rows[:-1]):
        for j,c in enumerate(columns[:-1]):
            arr.append((rows[i] + (rows[i+1]-rows[i])//2,columns[j]+(columns[j+1]-columns[j])//2))
    return arr

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

    new_corners = np.array([index_to_new_corner[index] for index in range(len(corners))])
    ##############

    # find and apply homography to straighten the corners.
    h, status = cv.findHomography(corners, new_corners)
    new_perspective = cv.warpPerspective(img, h, img.shape[:2])

    ax = (max_x-min_x)//30
    ay = (max_y-min_y)//30
    cropped_img = scaleImg(new_perspective[min_y-ay:max_y+ay,min_x-ax:max_x+ax])



    grid_width = 960
    grid_height = 960
    grid_area = grid_width*grid_height

    rows = np.arange(30, 930, 100)
    columns = np.arange(30, 930, 100)


    #find and predict digits in the new image
    denoised = cv.fastNlMeansDenoisingColored(cropped_img,None,10,10,7,21)
    gray = cv.cvtColor(denoised, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (5,5), 0).astype('uint8')
    thresh2 = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 21, 3)
    my_contours_cropped, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]

    #
    # cv.imshow(str(cropped_img.shape), cropped_img)
    # cv.waitKey(0)
    # cv.imshow('thresh2', thresh2)
    # cv.waitKey(0)
    #


###############################finding all cells and scanning cell by cell###########################################################################
    # cv.imshow(str(cropped_img.shape), cropped_img)
    # cv.waitKey(0)
    # cv.imshow('thresh2', thresh2)
    # cv.waitKey(0)
    #
    #
    # #https://stackoverflow.com/questions/59182827/how-to-get-the-cells-of-a-sudoku-grid-with-opencv
    # cnts = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    # cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    # for c in cnts:
    #     area = cv.contourArea(c)
    #     if area < 5000:
    #         cv.drawContours(thresh2, [c], -1, (0,0,0), -1)
    # cv.imshow('thresh 2', thresh2)
    # cv.waitKey(0)
    #
    # thresh3 = cv.adaptiveThreshold(thresh2, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 41, 1)
    # my_contours_cropped, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    #
    # cv.imshow('thresh 3', thresh3)
    # cv.waitKey(0)
    #
    # vertical_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1,10))
    # thresh4 = cv.morphologyEx(thresh3, cv.MORPH_CLOSE, vertical_kernel, iterations=9)
    #
    # cv.imshow('thresh4', thresh4)
    # cv.waitKey(0)
    #
    #
    # horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (10,1))
    # thresh5 = cv.morphologyEx(thresh4, cv.MORPH_CLOSE, horizontal_kernel, iterations=4)
    #
    # cv.imshow('thresh5', thresh5)
    # cv.waitKey(0)

    # invert = 255 - thresh4
    # cnts = cv.findContours(invert, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    # cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    # (cnts, _) = contours.sort_contours(cnts, method="top-to-bottom")
    # cv.imshow('invert', invert)
    # cv.waitKey(0)
    #
    # sudoku_rows = []
    # row = []
    # for (i, c) in enumerate(cnts, 1):
    #     area = cv.contourArea(c)
    #     if  area < 50000:
    #         row.append(c)
    #         if i % 9 == 0:
    #             (cnts, _) = contours.sort_contours(row, method="left-to-right")
    #             sudoku_rows.append(cnts)
    #             print(len(row))
    #             row = []
    #
    # print(len(sudoku_rows))
    #
    # # Iterate through each box
    # for row in sudoku_rows:
    #     for c in row:
    #         mask = np.zeros(cropped_img.shape, dtype=np.uint8)
    #         cv.drawContours(mask, [c], -1, (255,255,255), -1)
    #         result = cv.bitwise_and(cropped_img, mask)
    #         result[mask==0] = 255
    #         # cv.imshow(str(cv.contourArea(c)), result)
    #         # cv.waitKey(0)
    #
    # cv.imshow(str(cropped_img.shape), thresh2)
    # cv.waitKey(0)

##########################################################################################################


##################################looking for one cell at a time #################################################
    # for c in columns:
    #     cv.line(cropped_img, (c,30), (c,930),(0,255,0),5)
    # for r in rows:
    #     cv.line(cropped_img, (30,r), (930,r),(0,255,0),5)
    # cv.imshow('thresh2', cropped_img)
    # cv.waitKey(0)
    #
    # for j,c in enumerate(columns):
    #     for i,r in enumerate(rows):
    #         cropped_cell = denoised[c-30:c+130, r-30:r+130]
    #         gray = cv.cvtColor(cropped_cell, cv.COLOR_BGR2GRAY)
    #         gaus = cv.GaussianBlur(gray, (5,5), 0).astype('uint8')
    #         cell_thresh = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2)
    #         invert = 255 - cell_thresh
    #         cell_contours, _ = cv.findContours(invert, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    #
    #         largest_cell_contour_area = max([cv.contourArea(c) for c in cell_contours])
    #         outside_cell_contour = [c for c in cell_contours if cv.contourArea(c) == largest_cell_contour_area][0]
    #         corners = cv.approxPolyDP(outside_cell_contour,0.01*cv.arcLength(outside_cell_contour,True),True)
    #         M = cv.moments(outside_cell_contour)
    #         cX = int(M["m10"] / M["m00"])
    #         cY = int(M["m01"] / M["m00"])
    #         # cv.drawContours(cropped_cell,[corners],0,(0,0,0),-1)
    #         cv.circle(cropped_cell, (cX, cY), 7, (0, 255, 0), -1)
    #         cv.imshow('cropped_cell', cropped_cell)
    #         cv.waitKey(0)
    #
    #
    #
    # cells_centers = get_cells_centers(rows,columns)
    # for (x,y) in cells_centers:
    #         a = 80 #perspective increase around the grid cell
    #         cropped_cell = denoised[max(0,x-a):min(x+a,grid_width), max(0,y-a):min(y+a,grid_height)]
    #         gray = cv.cvtColor(cropped_cell, cv.COLOR_BGR2GRAY)
    #         gaus = cv.GaussianBlur(gray, (5,5), 0).astype('uint8')
    #         cell_thresh = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2)
    #         invert = 255 - cell_thresh
    #         cell_contours, _ = cv.findContours(invert, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    #
    #         largest_cell_contour_area = max([cv.contourArea(c) for c in cell_contours])
    #         outside_cell_contour = [c for c in cell_contours if cv.contourArea(c) == largest_cell_contour_area][0]
    #         corners = cv.approxPolyDP(outside_cell_contour,0.01*cv.arcLength(outside_cell_contour,True),True)
    #         M = cv.moments(outside_cell_contour)
    #         cX = int(M["m10"] / M["m00"])
    #         cY = int(M["m01"] / M["m00"])
    #         # cv.drawContours(cropped_cell,[corners],0,(0,0,0),-1)
    #         cv.circle(cropped_cell, (cX, cY), 7, (0, 255, 0), -1)
    #         cv.imshow('cropped_cell', cropped_cell)
    #         cv.waitKey(0)

#########################################################################################



    area_range = list(range(200,2700))
    height_range = list(range(30,90))
    width_range = list(range(15,60))

    predictor.load_model()
    imsize = predictor.getIMSIZE()

    sudoku_numbers = np.zeros((9,9), dtype=int)
    cells_centers = get_cells_centers(rows,columns)

    for cnt in my_contours_cropped:
        area = int(cv.contourArea(cnt))
        if area in area_range:
            [x,y,w,h] = cv.boundingRect(cnt)
            if h in height_range and w in width_range and 4>h/w>1.3:
                digit = thresh2[y:y+h,x:x+w]
                # cv.imshow(str(area)+' '+str(h)+' '+str(w)+ ' (' + str(x)+ ',' + str(y)+')', digit)
                # cv.waitKey(0)
                digit = pad_and_resize(digit,imsize)
                predicted = predictor.predict([digit])
                i,j = find_cell(rows, columns ,x,y)
                sudoku_numbers[i][j] = str(predicted[0])

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
