import os
from glob import glob
import shutil
from pathlib import Path
import argparse
import pdf_utils

def main():
    # read args
    ap = argparse.ArgumentParser(description="Process PDFs (add write permissions; remove watermarks; split pages).")
    ap.add_argument("--folder", required=True)
    ap.add_argument("--inplace", required=False, type=int, default=0)
    ap.add_argument("--write", required=False, type=int, default=1)
    ap.add_argument("--no_watermark", required=False, type=int, default=1)
    ap.add_argument("--split_pages", required=False, type=int, default=1)
    args = ap.parse_args()
    folder = args.folder
    inplace = bool(args.inplace)
    write = bool(args.write)
    no_watermark = bool(args.no_watermark)
    split_pages = bool(args.split_pages)
    if not os.path.isdir(folder):
        raise Exception(f"--folder `{folder}` is not a valid directory.")
    
    # read PDFs
    pdf_files = glob('*.pdf', root_dir=folder)

    # if not inplace, copy folder
    if not inplace:
        out_folder = Path(folder) / "cleaned"
        os.makedirs(out_folder, exist_ok=True)
        for pdf_file in pdf_files:
            pdf_path = Path(folder) / pdf_file
            out_path = out_folder / pdf_file
            shutil.copy(pdf_path, out_path)
        folder = out_folder
    
    # process PDFs
    for pdf_file in pdf_files:
        pdf_path = Path(folder) / pdf_file
        try:
            print(f"Processing {pdf_path}...")

            print("Adding write permissions...")
            if write:
                pdf_utils.add_write_permissions(pdf_path)
            else:
                print("Skipped")

            print("Removing watermarks...")
            if no_watermark:
                pdf_utils.remove_watermarks_and_text_with_pikepdf(
                    pdf_path=pdf_path, 
                    inplace=True,
                    remove_watermarks=True, 
                    phrase_to_remove=None
                )
            else:
                print("Skipped")

            print("Split pages in 2...")
            if split_pages:
                pdf_utils.split_pages_horizontally(pdf_path, inplace=True)
            else:
                print("Skipped")
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    main()