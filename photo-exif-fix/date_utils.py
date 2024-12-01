import os
import datetime
import glob

# !pip install pymediainfo
# !pip install pymediainfo

from pymediainfo import MediaInfo
import subprocess
import pywintypes
import win32file
import win32con

def _read_file_dates(filepath):
    dates = {
        'creation_time': None,
        'modification_time': None,
        'access_time': None,
        'recorded_date': None,
        'encoded_date': None,
        'tagged_date': None
    }

    try:       
        # File system dates
        dates['creation_time'] = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
        dates['modification_time'] = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
        dates['access_time'] = datetime.datetime.fromtimestamp(os.path.getatime(filepath))    
    except Exception as e:
        print(f"Broken filepath {filepath} on reading file dates: {e}")

    try:
        media_info = MediaInfo.parse(filepath)

        parse_date = lambda date_str: datetime.datetime.fromisoformat(date_str.replace(" UTC", "+00:00")).replace(tzinfo=None) if date_str else None

        for track in media_info.tracks:
            if track.track_type == "General":
                if hasattr(track, "recorded_date"):
                    dates['recorded_date'] = parse_date(track.recorded_date)
                if hasattr(track, "encoded_date"):
                    dates['encoded_date'] = parse_date(track.encoded_date)
                if hasattr(track, "tagged_date"):
                    dates['tagged_date'] = parse_date(track.tagged_date)
                break
    except Exception as e:
        print(f"Broken filepath {filepath} on reading media dates: {e}")

    return dates

def _get_correct_dt_to_apply(filepath, filename_dt):
    # read the dates recorded in filesystem
    dates = _read_file_dates(filepath)
    last_modification_dt = dates['modification_time']
    last_acc_dt = dates['access_time']

    last_modified_same_as_filename_dt = (filename_dt.year == last_modification_dt.year) and (filename_dt.month == last_modification_dt.month) and (filename_dt.day == last_modification_dt.day)
    last_access_same_as_filename_dt = (filename_dt.year == last_acc_dt.year) and (filename_dt.month == last_acc_dt.month) and (filename_dt.day == last_acc_dt.day)

    if last_access_same_as_filename_dt:
        return None # everything is fine
    else:
        if last_modified_same_as_filename_dt:
            return last_modification_dt
        else:
            return filename_dt

def _set_date_pywin(filepath, target_date):
    """Set creation, modification, and access times for a file."""
    try:
        pywin_time = pywintypes.Time(target_date)
        handle = win32file.CreateFile(
            str(filepath),
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None,
        )
        win32file.SetFileTime(handle, pywin_time, None, pywin_time)
        win32file.CloseHandle(handle)
        os.utime(filepath, (target_date.timestamp(), target_date.timestamp()))
    except Exception as e:
        print(f"Error {type(e)} with PYWIN on file {filepath}: {e}")

def _set_date_ffmpeg(filepath, dt):
    """
    Sets the metadata date of a media file.
    """
    # Format date for ffmpeg metadata
    ffmpeg_date = dt.strftime(f'%Y-%m-%dT%H:00:00')

    # Temporary file for output
    _, ext = os.path.splitext(filepath)
    temp_file = filepath.replace(ext, f"_temp{ext}")

    # Use ffmpeg to update the creation_time metadata

    ffmpeg_path = "./ffmpeg-2024-11-28-git-bc991ca048-essentials_build/bin/ffmpeg.exe"
    if not os.path.exists(ffmpeg_path):
        raise Exception(f"FFMPEG not found in path ({ffmpeg_path}). Download it from https://www.gyan.dev/ffmpeg/builds/")
    try:
        subprocess.run([
            ffmpeg_path, "-i", filepath, 
            "-map_metadata", "0",
            "-metadata", f"creation_time={ffmpeg_date}",
            "-metadata", f"modification_time={ffmpeg_date}",
            "-c", "copy", temp_file
        ], check=True)
        # Replace the original file with the updated one
        os.replace(temp_file, filepath)
    except Exception as e:
        print(f"Error {type(e)} with FFMPEG on file {filepath}: {e}")

def _fix_date(filepath):
    filename = os.path.basename(filepath)
    filename_dt = datetime.datetime(year=int(filename[0:4]), month=int(filename[5:7]), day=int(filename[8:10]))

    dt_to_apply = _get_correct_dt_to_apply(filepath, filename_dt)
    if dt_to_apply is not None:
        _set_date_ffmpeg(filepath=filepath, dt=dt_to_apply)
        _set_date_pywin(filepath=filepath, target_date=dt_to_apply)

def process_files(folder_path, extensions_to_process = ['.jpg', '.png', '.mp4']):
    if not os.path.isdir(folder_path):
        raise Exception(f"Folder {folder_path} not found")
    
    filepaths = [
        filepath 
        for filepath in glob.glob(os.path.join(folder_path, '**'), recursive=True) 
        if os.path.isfile(filepath)
    ]

    good_filepaths = []
    bad_filepaths = []
    for filepath in filepaths:
        _, ext = os.path.splitext(filepath)
        if ext.lower() in extensions_to_process:
            good_filepaths.append(filepath)
        else:
            bad_filepaths.append(filepath)
    
    if len(bad_filepaths) > 0:
        print("Found files with invalid filepaths")
        for filepath in bad_filepaths:
            print(filepath)
        stop = input("Vuoi continuare? S/N").upper() == 'S'
    else:
        stop = False

    if not stop:
        for filepath in good_filepaths:
            _fix_date(filepath)