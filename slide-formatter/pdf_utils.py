import os
from glob import glob
from pathlib import Path
import unicodedata

# pip install pikepdf==9.*
import pikepdf
from pikepdf import Name, Stream, Array, String, Dictionary

def add_write_permissions(pdf_path):   
    pdf = pikepdf.open(pdf_path, allow_overwriting_input=True)
    pdf.save(pdf_path)

def _add_suffix(path: Path, suffix: str) -> Path:
    """Adds a suffix before the file extension."""
    return path.with_name(f"{path.stem}{suffix}.pdf")

def remove_watermarks_with_pikepdf(pdf_path: Path, inplace: bool) -> Path:
    def _is_watermark_present(xobj_dict: Dictionary) -> bool:
        """Checks if the Form XObject has watermark metadata or characteristics."""

        # Detect Adobe watermark metadata flag
        piece = xobj_dict.get("/PieceInfo", None)
        if isinstance(piece, Dictionary):
            for _, v in piece.items():
                if isinstance(v, Dictionary) and v.get("/Private", None) == Name("/Watermark"):
                    return True
        return False

    # counters
    removed_watermarks = 0

    # setup in/out paths
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)
    out_path = _add_suffix(pdf_path, "_clean")

    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        # Iterate all objects in the pdf
        for obj in list(pdf.objects):
            # consider only Form XObject
            if not isinstance(obj, Stream) or obj.get("/Subtype", None) != Name("/Form"):
                continue
                        
            # if the object is a watermark, remove it
            if _is_watermark_present(obj):
                # replace the item with an empty object
                obj.write(b"q Q\n")

                removed_watermarks += 1
                continue
            
        print(f"Removed {removed_watermarks} watermark XObject(s)")
        pdf.save(out_path)

        if inplace:
            os.remove(pdf_path)
            os.rename(out_path, pdf_path)

        return out_path
    
def _simplify_pdf_structure(pdf_path: Path) -> Path:
    """Simplify the PDF structure using qpdf, to make it easier to edit as text."""
    
    pdf_path = Path(pdf_path)

    import subprocess
    cmd = subprocess.run(
        f'qpdf --qdf --object-streams=disable --replace-input "{pdf_path}"',
        shell=True,
        capture_output=True,
        text=True
    )
    if cmd.returncode != 0:
        raise Exception(f"Error simplifying PDF structure with qpdf: {cmd.stderr}")

    return pdf_path

def _remove_text_with_qpdf(pdf_path, text_to_remove):
    # NOTE: NOT IMPLEMENTED YET; HERE'S THE LOGIC
    
    # STEPS:
    # - Go to qpdf github page (https://github.com/qpdf/qpdf/releases)
    # - Download the windows installer (qpdf-12.2.0-msvc64.exe)
    # - Add to user PATH (C:\Program Files\qpdf 12.2.0\bin)
    # - Simplify the PDF text: qpdf --qdf --object-streams=disable my_pdf.pdf my_pdf_simple.pdf
    # - Open with a text editor the simplified PDF
    # - Search of a single word of the text the remove, to find the block with the bad text
    # - Manually delete the block (or automate the search & delete with a script)

    # EXAMPLE:
    # - Text to remove: `Università degli studi Guglielmo Marconi`
    # - How it appears in the simplified PDF:
    # ```
    # %% Original object ID: 126 0
    # 38 0 obj
    # <<
    # /BBox [
    #     0
    #     -48
    #     856.36
    #     4.80029
    # ]
    # /LastModified (D:20240724105529+02'00')
    # /Matrix [
    #     1
    #     0
    #     0
    #     1
    #     0
    #     0
    # ]
    # /OC 146 0 R
    # /PieceInfo <<
    #     /ADBE_CompoundType <<
    #     /DocSettings 147 0 R
    #     /LastModified (D:20240724105529+02'00')
    #     /Private /Watermark
    #     >>
    # >>
    # /Resources 149 0 R
    # /Subtype /Form
    # /Length 39 0 R
    # >>
    # stream
    # 0 g 0 G 0 i 0 J []0 d 0 j 1 w 10 M 0 Tc 0 Tw 100 Tz 0 TL 0 Tr 0 Ts
    # BT
    # /Arial 48 Tf
    # 0 g
    # 0 -37.898 Td
    # (Universit\340 ) Tj
    # 226.734 0 Td
    # (degli ) Tj
    # 114.75 0 Td
    # (studi ) Tj
    # 114.727 0 Td
    # (Guglielmo ) Tj
    # 229.43 0 Td
    # (Marconi) Tj
    # ET
    # endstream
    # endobj
    # ```

    pass

def split_pages_horizontally(pdf_path: str | Path, inplace: bool) -> Path:
    """
    Create a new PDF with each original page split into two pages:
    TOP half first, then BOTTOM half. Lossless (CropBox only).
    """
    pdf_path = Path(pdf_path)
    out_path = _add_suffix(pdf_path, "_split")

    with pikepdf.open(pdf_path, allow_overwriting_input=True) as src:
        dst = pikepdf.Pdf.new()

        for src_page in src.pages:
            # Use existing visible box if any, otherwise MediaBox
            box = src_page.obj.get("/CropBox", src_page.obj.get("/MediaBox"))
            x0, y0, x1, y1 = map(float, box)
            mid_y = y0 + (y1 - y0) / 2.0

            # Import the same source page twice into dst
            dst.pages.append(src_page)  # will import/copy into dst
            dst.pages.append(src_page)

            # Get the two newly added pages
            p_top = dst.pages[-2]
            p_bot = dst.pages[-1]

            # Set crop boxes: TOP first, then BOTTOM
            p_top.obj["/CropBox"] = Array([x0, mid_y, x1, y1])
            p_bot.obj["/CropBox"] = Array([x0, y0,   x1, mid_y])

        dst.save(out_path)

    if inplace:
        os.remove(pdf_path)
        os.rename(out_path, pdf_path)

    return out_path

def read_pdf_text(pdf_path: Path):
    # !pip install pypdf
    import pypdf

    path = Path(pdf_path)
    pdf = pypdf.PdfReader(path)

    print(f"Reading contents of PDF {path}")
    for idx, page in enumerate(pdf.pages):
        print(f"--- PAGE {idx} ---")
        print(page.extract_text())