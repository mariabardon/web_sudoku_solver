from .digit_predictor import Predictor as predictor
from .solver_files import ASP_interface
import cv2 as cv
import numpy as np
import sys, timeit

global count

count = 0
showImages = False
showAllDigits = False
def pad_and_resize(digit,imsize):
    s = imsize//9
    digit = cv.resize(digit, (5*s,7*s))
    digit = cv.copyMakeBorder(digit, s, imsize-8*s, 2*s, imsize-7*s,\
                              borderType = cv.BORDER_CONSTANT, value=[0,0,0] )
    return digit

def scaleImg(img,dim):
    img = cv.resize(img, dim, interpolation = cv.INTER_AREA)
    return img

def find_cell(x_array, y_array ,c):
    [x,y] = c
    i = max([i for i,x_coor in enumerate(x_array) if x_coor < x])
    j = max([j for j,y_coor in enumerate(y_array) if y_coor < y])
    return (i,j)

def scan_image(img):
    min_area, max_area = 150, 3000
    min_height, max_height = 30, 85

    grid_width = 900
    grid_height = 900
    grid_area = grid_width*grid_height
    rows = np.arange(0, grid_height, grid_height//9)
    columns = np.arange(0, grid_width, grid_width//9)

    s = img.shape
    dim = (1000*s[1]//s[0],1000)
    img = scaleImg(img,dim)
    edited_img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gauss = cv.GaussianBlur(edited_img, (9,9), 0)
    edited_img = cv.adaptiveThreshold(gauss, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 2)
    drawContoursAndShow(edited_img,[])


    d=4
    edited_img = cv.morphologyEx(edited_img, cv.MORPH_CLOSE, kernel=np.ones((d,d),np.uint8))

    # d = 4
    # vertical_kernel = cv.getStructuringElement(cv.MORPH_RECT, (1,d))
    # edited_img = cv.morphologyEx(edited_img, cv.MORPH_CLOSE, vertical_kernel, iterations=1)
    # horizontal_kernel = cv.getStructuringElement(cv.MORPH_RECT, (d,1))
    # edited_img = cv.morphologyEx(edited_img, cv.MORPH_CLOSE, horizontal_kernel, iterations=1)
    # drawContoursAndShow(edited_img,[])


    my_contours, _ = cv.findContours(edited_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)[-2:]
    largest_area = max([cv.contourArea(c) for c in my_contours])
    sudoku_grid_contour = [c for c in my_contours if cv.contourArea(c) == largest_area][0]
    # drawContoursAndShow(img,sudoku_grid_contour)


    vertices = cv.approxPolyDP(sudoku_grid_contour,0.08*cv.arcLength(sudoku_grid_contour,True),True)
    # drawContoursAndShow(img,vertices)
    vertices=np.squeeze(vertices)

    a = 9
    while len(vertices) <4:
        a = a * 2 + 1
        edited_img = cv.adaptiveThreshold(gauss, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, a, 2)
        my_contours, _ = cv.findContours(edited_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)[-2:]
        largest_area = max([cv.contourArea(c) for c in my_contours])
        sudoku_grid_contour = [c for c in my_contours if cv.contourArea(c) == largest_area][0]
        vertices = cv.approxPolyDP(sudoku_grid_contour,0.08*cv.arcLength(sudoku_grid_contour,True),True)
        # drawContoursAndShow(img,my_contours)
        # drawContoursAndShow(img,vertices)
        vertices = np.squeeze(vertices)

    ################# identifying_corners
    top_left_index = np.argmax([-sum(c) for c in vertices])
    bottom_right_index = np.argmax([sum(c) for c in vertices])
    bottom_left_index = np.argmax([c[1]-c[0] for c in vertices])
    top_right_index = np.argmax([c[0]-c[1] for c in vertices])
    corners = np.array([vertices[top_left_index],\
                    vertices[bottom_right_index],\
                    vertices[bottom_left_index],\
                    vertices[top_right_index]])

    min_x = min([c[0] for c in corners])
    min_y = min([c[1] for c in corners])
    max_x = max([c[0] for c in corners])
    max_y = max([c[1] for c in corners])

    index_to_new_corner = {top_left_index:[min_x,min_y],\
                           bottom_right_index:[max_x, max_y],\
                           bottom_left_index:[min_x, max_y],\
                           top_right_index:[max_x,min_y]}

    new_corners = np.array([index_to_new_corner[top_left_index],\
                    index_to_new_corner[bottom_right_index],\
                    index_to_new_corner[bottom_left_index],\
                    index_to_new_corner[top_right_index]])

    # find and apply homography to straighten the vertices.
    h, status = cv.findHomography(corners, new_corners)
    new_perspective = cv.warpPerspective(img, h, (img.shape[1],img.shape[0]))
    new_perspective = scaleImg(new_perspective[min_y:max_y,min_x:max_x], (grid_width,grid_height))
    ###########################################################################################

    #finding and predict digits in the new image
    final_thresh, my_contours, final_max_height  = guess_digits_contours(new_perspective, min_height, max_height, min_area, max_area)
    centers = [[cv.boundingRect(cnt)[0]+cv.boundingRect(cnt)[-2]//2,cv.boundingRect(cnt)[1]+cv.boundingRect(cnt)[-1]//2] for cnt in my_contours]
    cells = list(set([find_cell(rows,columns,c) for c in centers]))
    drawContoursAndShow(final_thresh,[])

    if(len(centers)>len(cells) or len(cells)<17): #if not many contours have been found try with inverse image
        # print([find_cell(rows,columns,c) for c in centers])
        # sys.stdout.flush()
        new_perspective = 255-new_perspective
        final_thresh, my_contours, final_max_height = guess_digits_contours(new_perspective, min_height, max_height, min_area, max_area)




    # final_thresh = cv.fastNlMeansDenoisingColored(new_perspective,None,10,10,7,21)
    # final_thresh = cv.cvtColor(final_thresh, cv.COLOR_BGR2GRAY)
    # final_thresh = cv.GaussianBlur(final_thresh, (11,11), 0).astype('uint8')
    # final_thresh = cv.adaptiveThreshold(final_thresh, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 29, 2)
    # drawContoursAndShow(final_thresh,[])

    # d = int(final_max_height/6)
    # drawContoursAndShow(edited_img,[])
    # kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE,(d,d))
    # final_thresh = cv.morphologyEx(final_thresh, cv.MORPH_CLOSE, kernel=np.ones((d,d),np.uint8))


    predictor.load_model()
    sudoku_numbers = np.zeros((9,9), dtype=int)
    for cnt in my_contours:
        [x,y,w,h] = cv.boundingRect(cnt)
        i, j = (x+w//2)//100 , (y+h//2)//100
        digit = final_thresh[y:y+h,x:x+w]
        # digit = cv.morphologyEx(digit, cv.MORPH_CLOSE, kernel)
        digit = pad_and_resize(digit,predictor.getIMSIZE())
        predicted = predictor.predict([digit])
        sudoku_numbers[i][j] = str(predicted[0])
        if showAllDigits:
            cv.imshow(str(predicted)+' '+str((i+1,j+1)),digit)
            cv.waitKey(0)
    try:
        solution = solve_sudoku(sudoku_numbers)
    except Exception as e:
        raise e
    return solution, sudoku_numbers, new_perspective

def solve_sudoku(sudoku_numbers):
    asp_lines = []
    for i in range(9):
        for j in range(9):
            num = sudoku_numbers[i][j]
            if num != 0:
                asp_lines.append('value(cell({},{}),{}).'.format(i+1,j+1,int(sudoku_numbers[i][j])))
    solution_matrix = np.zeros((9,9), dtype=int)
    solution_matrix[sudoku_numbers!=0] = sudoku_numbers[sudoku_numbers!=0]
    print('solving it')
    try:
        solution = ASP_interface.solve(asp_lines)
    except RuntimeError as err:
        raise RuntimeError('Oops... Unable to find all digits in this sudoku. It may be rotated or unfocused. Please try again.')
    if solution == ['']:
        raise Exception('Oops... I cannot see well the sudoku grid in the image')
    for e in solution:
        #i and j go from 0 to 8, but answer goes from 1 to 9
        [i,j,digit] = np.add( [int(c) for c in e if c.isdigit()] , [-1,-1,0] )
        solution_matrix[i][j]=digit
    return solution_matrix, sudoku_numbers

def guess_digits_contours(new_perspective, min_height, max_height, min_area, max_area, reverse=False):
    ## create threshold image and remove too large or too small contours
    edited_img = cv.fastNlMeansDenoisingColored(new_perspective,None,10,10,7,21)
    edited_img = cv.cvtColor(edited_img, cv.COLOR_BGR2GRAY)
    edited_img = cv.GaussianBlur(edited_img, (11,11), 0).astype('uint8')
    if reverse: edited_img = 255 - edited_img
    edited_img = cv.adaptiveThreshold(edited_img, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 13, 2)
    my_contours, _ = cv.findContours(edited_img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    my_contours = [c for c in my_contours if min_height < cv.boundingRect(c)[-1] < max_height and min_area < cv.contourArea(c) < max_area]
    # drawContoursAndShow(new_perspective,my_contours)

    ## with remaining contours, we assume that most common height bin of the heights histogram
    ## will represent the aprox height of our digits, since all digits will have very simmilar height
    heights = [cv.boundingRect(c)[-1]  for c in my_contours]
    hist, bin_edges = np.histogram(heights,bins=100)
    largest_bin = np.argmax(hist)
    final_max_height = int(bin_edges[largest_bin+1])

    ## knowing the most common height range we calculate the
    ## the variable d, used to close the thresholded image.

    d = final_max_height//8
    # kernel=np.ones((d,d),np.uint8)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE,(d,d))
    drawContoursAndShow(edited_img,[])
    edited_img = cv.morphologyEx(edited_img,cv.MORPH_CLOSE,kernel)
    drawContoursAndShow(edited_img,[])

    ## close the shapes in the threshold image using d as a kernel and find new contours
    ## filter out the contours that are not in the new height range
    ## and the contours that have shape that is too wide or too narrow for its height
    # edited_img = cv.morphologyEx(edited_img, cv.MORPH_CLOSE, kernel)
    my_contours, _ = cv.findContours(edited_img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    my_contours = [c for c in my_contours if final_max_height-2*d < cv.boundingRect(c)[-1] < final_max_height+2*d \
                                                and 4>cv.boundingRect(c)[-1]/cv.boundingRect(c)[-2]>0.9 \
                                                and min_area < cv.contourArea(c)]

    # drawContoursAndShow(edited_img,[])
    drawContoursAndShow(new_perspective,my_contours)
    return edited_img,my_contours, final_max_height

## This method is build for the purpose of debugging and finding errors.
def drawContoursAndShow(image,contours):
    global count
    if showImages == False: return
    img = image.copy()
    cv.drawContours(img, contours, -1, (0,255,0), 2)
    cv.imshow(str(count),img)
    cv.waitKey(0)
    count += 1
