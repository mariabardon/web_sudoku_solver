from .digit_predictor import Predictor as predictor
from .solver_files import ASP_interface
import cv2 as cv
import numpy as np

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

def scaleImg(img,dim):
    img = cv.resize(img, dim, interpolation = cv.INTER_AREA)
    return img

def find_cell(x_array, y_array ,c):
    [x,y] = c
    i = max([i for i,x_coor in enumerate(x_array) if x_coor < x])
    j = max([j for j,y_coor in enumerate(y_array) if y_coor < y])
    return (i,j)

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
    area_range = list(range(150,2700))
    height_range = list(range(30,90))
    width_range = list(range(15,60))
    grid_width = 900
    grid_height = 900
    grid_area = grid_width*grid_height
    rows = np.arange(0, grid_height, grid_height//9)
    columns = np.arange(0, grid_width, grid_width//9)

    s = img.shape
    dim = (2000*s[1]//s[0],2000)
    # dim = (900,900)
    img = scaleImg(img,dim)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (9,9), 0)
    thresh = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 11, 2)
    p = 4
    thresh = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel=np.ones((p,p),np.uint8))
    my_contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)[-2:]
    # cv.imshow('thresh',thresh)
    # cv.waitKey(0)

    # get contour with largest area (which is sudoku grid outside border),
    # approximate as polygonal shape
    largest_area = max([cv.contourArea(c) for c in my_contours])
    sudoku_grid_contour = [c for c in my_contours if cv.contourArea(c) == largest_area][0]

    # test = cv.drawContours(img, sudoku_grid_contour, -1, (0,255,0),3)
    # cv.imshow('contour grid',test)
    # cv.waitKey(0)
    ############## from grid vertices to new grid vertices applying perspective rectification
    ###########################################################################################
    vertices = cv.approxPolyDP(sudoku_grid_contour,0.01*cv.arcLength(sudoku_grid_contour,True),True)
    vertices=np.squeeze(vertices)

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
    cropped_grid = scaleImg(new_perspective[min_y:max_y,min_x:max_x], (grid_width,grid_height))
    ###########################################################################################



    #find and predict digits in the new image
    denoised = cv.fastNlMeansDenoisingColored(cropped_grid,None,10,10,7,21)
    gray = cv.cvtColor(denoised, cv.COLOR_BGR2GRAY)
    gaus = cv.GaussianBlur(gray, (11,11), 0).astype('uint8')

    thresh2 = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 2)
    my_contours_cropped, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    max_area = np.max([cv.contourArea(c)  for c in my_contours_cropped if cv.contourArea(c) in area_range])
    d = max_area.astype(int)//250
    thresh3 = cv.morphologyEx(thresh2, cv.MORPH_CLOSE, kernel=np.ones((d,d),np.uint8))
    my_contours_cropped, _ = cv.findContours(thresh3, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
    filtered_cnt = [cnt for cnt in my_contours_cropped if int(cv.contourArea(cnt)) in area_range]

    filtered_cnt = [c for c in filtered_cnt if cv.boundingRect(c)[-1] in height_range and cv.boundingRect(c)[-2] in width_range and 4>cv.boundingRect(c)[-1]/cv.boundingRect(c)[-2]>1.2 ]
    try:
        max_h = np.max([cv.boundingRect(c)[-1]  for c in filtered_cnt if cv.contourArea(c) in area_range])
    except Exception as e:
        raise Exception('Oops... Unable to find the grid of the sudoku. Please try again.')
    filtered_cnt = [c for c in filtered_cnt if cv.boundingRect(c)[-1] > max_h*0.7]
    centers = [[cv.boundingRect(cnt)[0]+cv.boundingRect(cnt)[-2]//2,cv.boundingRect(cnt)[1]+cv.boundingRect(cnt)[-1]//2] for cnt in filtered_cnt]
    cells = list(set([find_cell(rows,columns,c) for c in centers]))
    if(len(centers)>len(cells) or len(cells)<17): #if not many contours have been found try with inverse image
        gaus = 255-gaus
        thresh2 = cv.adaptiveThreshold(gaus, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 9, 2)
        my_contours_cropped, _ = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[-2:]
        max_area = np.max([cv.contourArea(c)  for c in my_contours_cropped if cv.contourArea(c) in area_range])
        d = max_area.astype(int)//250
        thresh3 = cv.morphologyEx(thresh2, cv.MORPH_CLOSE, kernel=np.ones((d,d),np.uint8))
        filtered_cnt = [cnt for cnt in my_contours_cropped if int(cv.contourArea(cnt)) in area_range]
        filtered_cnt = [c for c in filtered_cnt if cv.boundingRect(c)[-1] in height_range and cv.boundingRect(c)[-2] in width_range and 4>cv.boundingRect(c)[-1]/cv.boundingRect(c)[-2]>1.2 ]
        try:
            max_h = np.max([cv.boundingRect(c)[-1]  for c in filtered_cnt if cv.contourArea(c) in area_range])
        except Exception as e:
            raise Exception('Oops... Unable to find the grid of the sudoku. Please try again.')
        filtered_cnt = [c for c in filtered_cnt if cv.boundingRect(c)[-1] > max_h*0.7]

    predictor.load_model()
    sudoku_numbers = np.zeros((9,9), dtype=int)
    for cnt in filtered_cnt:
        [x,y,w,h] = cv.boundingRect(cnt)
        ctr = [x+w//2,y+h//2]
        (i,j) = find_cell(rows, columns ,ctr)
        digit = thresh3[y:y+h,x:x+w]
        digit = pad_and_resize(digit,predictor.getIMSIZE())
        predicted = predictor.predict([digit])
        sudoku_numbers[i][j] = str(predicted[0])
        # cv.imshow(str((i,j)) + ' ' + str(predicted),digit)
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

    print('solving it')
    try:
        solution = ASP_interface.solve(asp_lines)
    except RuntimeError as err:
        raise RuntimeError('Oops... Unable to find all digits in this sudoku. It may be rotated or unfocused. Please try again.')


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
