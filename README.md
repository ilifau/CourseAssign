# CourseAssign

This is a python script that optimizes the course assignments for the CombiSuscription plugin of ILIAS:
https://github.com/ilifau/CombiSubscription



## Installation

- copy this directory to a machine with python3 installed
- run `pip install --no-cache-dir -r requirements.txt` in this directory
- create a folder `data` in this directory

## Usage

Export
- go to *Assignment / Export Data* in a CombiSubscription object of ILIAS
- choose the table format *raw data* and the file type *csv*
- export the data
- 
Calculation
- copy the exported csv file to the `data` folder on your machine
- run `run.sh`
- a file `data_solution.csv` will be created in the `data` folder
- edit the file and replace `,` by `;`

Import
- go to *Assignment / Import Data* in the CombiSubscription object
- select the created `data_solution.csv` file
- select *Assignments by IDs*
- add a comment to identify the import
- import the data
- go to *Saved Assignments* and compare the import with a calculation of the plugin