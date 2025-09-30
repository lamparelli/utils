import os
from glob import glob
from pathlib import Path
import subprocess
import codecs
import re

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

    cmd = subprocess.run(
        f'qpdf --qdf --object-streams=disable --replace-input "{pdf_path}"',
        shell=True,
        capture_output=True,
        text=True
    )
    if cmd.returncode != 0:
        raise Exception(f"Error simplifying PDF structure with qpdf: {cmd.stderr}")

    return pdf_path
    
def _revert_qpdf_simplification(pdf_path: Path) -> Path:    
    pdf_path = Path(pdf_path)

    cmd = subprocess.run(
        f'qpdf --object-streams=generate --stream-data=compress --linearize --replace-input "{pdf_path}"',
        shell=True,
        capture_output=True,
        text=True
    )
    if cmd.returncode != 0:
        raise Exception(f"Error simplifying PDF structure with qpdf: {cmd.stderr}")

    return pdf_path

def remove_text(pdf_path: Path, text_to_remove: str) -> Path:
    # define in/out paths
    pdf_path = Path(pdf_path)
    out_path = _add_suffix(path=pdf_path, suffix='_test')

    # simplify the pdf format with QPDF
    _simplify_pdf_structure(pdf_path=pdf_path)

    # define how to extract objects from the QPDF representation
    FIND_OBJECTS_REGEX = re.compile(rb'(?ms)^\s*(\d+)\s+\d+\s+obj\b.*?^\s*endobj\s*')
    
    # read input
    pdf_buffer = pdf_path.read_bytes()
    
    # init output
    out_buffer = []
    valid_data_start_idx = 0

    # for each object found, check if the object contains the bad phrase; if so, skip it
    for match in FIND_OBJECTS_REGEX.finditer(pdf_buffer):

        # check if the bad phrase is in the object
        object = pdf_buffer[match.start():match.end()]
        try:
            obj_text = codecs.decode(object, "unicode-escape")
            obj_contains_bad_text = all(
                word.lower() in obj_text.lower()
                for word in text_to_remove.split()
            )
            # TODO test why it's not seeing the bad text
        except Exception:
            obj_contains_bad_text = False

        # if the bad phrase is in the object, skip it from the output
        if obj_contains_bad_text:
            # keep everything up to the start of this bad object
            out_buffer.append(pdf_buffer[valid_data_start_idx:match.start()])
            # skip the bad object
            valid_data_start_idx = match.end()

    # tail (keep everything after the last removed object)
    out_buffer.append(pdf_buffer[valid_data_start_idx:])

    # join the output portions into a binary var 
    out_buffer = b"".join(out_buffer)

    # save the output
    out_path.write_bytes(out_buffer)

    # revert PDF structure to original
    _revert_qpdf_simplification(pdf_path=out_path)

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