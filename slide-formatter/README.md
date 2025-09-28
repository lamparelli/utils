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
python process_slides.py --folder C:\Users\my_user\path_to_folder --inplace 0 --write 1 --no_watermark 1 --split_pages 1
```

## Next steps

- Improve page splitting
    - current situation: the page with top half contains all the original page text, but just the top half visible (same for bottom half)
    - how to test: use pdf_utils.read_pdf_text() function to display the content of each page
    - goal: each page should contain just its' own stuff, to avoid confusing LLMs and text parsers

- Improve watermark removal
    - current situation
        - the watermark removal works only on some files (maybe on some the text is not marked as watermark)
        - the logic to delete a text is not working
    - goal: fix the delete text logic
    - how to test: check the pdf_utils._extract_text_from_object_stream() function to see if it's properly reading text