# Slide formatter

## Input 

A folder with a series of slides

## Output

Each slide:
- has write permissions (to add comments, highlights, etc)
- has the watermark removed
- is split into 2 pages (top half, bottom half)

## Usage example

1) Install python

2) Install dependencies
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

3) Run program
```
.\venv\Scripts\activate
python process_slides.py --folder C:\Users\my_user\path_to_folder --inplace 1 --write 1 --no_watermark 1 --split 1
```