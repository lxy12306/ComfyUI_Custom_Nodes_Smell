import os
from .function import smell_debug

def get_dir_and_prefix(BaseDirectory, FilenamePrefix1, FilenamePrefix2=None):
    Directory1 = BaseDirectory
    Directory2 = os.path.join(Directory1, FilenamePrefix1)
    Directory = Directory2
    if not os.path.exists(Directory1):
        os.makedirs(Directory1)
    if not os.path.exists(Directory2):
        os.makedirs(Directory2)

    _FilenamePrefix = FilenamePrefix1
    FilenamePrefix = _FilenamePrefix

    if not FilenamePrefix2 == None:
        Directory3 = os.path.join(Directory2, FilenamePrefix2)
        Directory = Directory3
        FilenamePrefix = f"{_FilenamePrefix}_{FilenamePrefix2}"
        if not os.path.exists(Directory3):
            os.makedirs(Directory3)

    smell_debug(Directory, FilenamePrefix)
    return Directory, FilenamePrefix

def smell_write_text_file(file, content, encoding="utf-8"):
    try:
        with open(file, 'w', encoding=encoding, newline='\n') as f:
            f.write(content)
    except OSError:
        smell_debug(f"{file} save failed")