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
python process_slides.py --folder C:\Users\my_user\path_to_folder --write 1 --no_watermark 1 --split_pages 1
```

## Next steps

- Improve watermark removal
    - current situation
        - the watermark removal works only on some files (maybe on some the text is not marked as watermark)
        - the logic to delete a text is not working (due to pikepdf not reading text correctly; pdf_utils._extract_text_from_object_stream() doesn't work)
    - goal: fix the delete text logic
    - how to fix: use the qpdf approach, to simplify the PDF and parse the simplified text accordingly; check pdf_utils._remove_text_with_qpdf() for info

- Improve page splitting
    - current situation: the page with top half contains all the original page text, but just the top half visible (same for bottom half)
    - how to test: use pdf_utils.read_pdf_text() function to display the content of each page
    - goal: each page should contain just its' own stuff, to avoid confusing LLMs and text parsers

## Explanation of QPDF setup and usage to remove text

STEPS:
- Go to qpdf github page (https://github.com/qpdf/qpdf/releases)
- Download the windows installer (qpdf-12.2.0-msvc64.exe)
- Add to user PATH (C:\Program Files\qpdf 12.2.0\bin)
- Simplify the PDF text: qpdf --qdf --object-streams=disable my_pdf.pdf my_pdf_simple.pdf
- Open with a text editor the simplified PDF
- Search of a single word of the text the remove, to find the block with the bad text
- Manually delete the block (or automate the search & delete with a script)

EXAMPLE:
- Text to remove: `Università degli studi Guglielmo Marconi`
- How it appears in the simplified PDF:
```
%% Original object ID: 126 0
38 0 obj
<<
/BBox [
    0
    -48
    856.36
    4.80029
]
/LastModified (D:20240724105529+02'00')
/Matrix [
    1
    0
    0
    1
    0
    0
]
/OC 146 0 R
/PieceInfo <<
    /ADBE_CompoundType <<
    /DocSettings 147 0 R
    /LastModified (D:20240724105529+02'00')
    /Private /Watermark
    >>
>>
/Resources 149 0 R
/Subtype /Form
/Length 39 0 R
>>
stream
0 g 0 G 0 i 0 J []0 d 0 j 1 w 10 M 0 Tc 0 Tw 100 Tz 0 TL 0 Tr 0 Ts
BT
/Arial 48 Tf
0 g
0 -37.898 Td
(Universit\340 ) Tj
226.734 0 Td
(degli ) Tj
114.75 0 Td
(studi ) Tj
114.727 0 Td
(Guglielmo ) Tj
229.43 0 Td
(Marconi) Tj
ET
endstream
endobj
```