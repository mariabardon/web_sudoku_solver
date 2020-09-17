## Sudoku Solver

This is a repository for the code used for this application: sudoku.rociogomez.com or at sudoku-web-application.heroku.com


The application will let you upload an image of a sudoku that has not been completed, and it will give you a solution of the sudoku.

For building this application I used four differnt parts:

1.  A function that processes an image, finds the sudoku grid in the image and exctracts the digits within the grid.
2.  Building and training a CNN model that predicts digits.
3.  An answer set program that solves the sudoku given the predicted digits, and their location in the grid.
4.  A Django web application constructed using the parts above.  
5.  Deploying the Django app in heroku. [Steps here](readme_links/deploying.md)
