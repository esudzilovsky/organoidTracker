# -*- coding: utf-8 -*-
"""
Created on Thu Jun 07 16:32:39 2018

@author: Edward
"""
from __future__ import print_function
import numpy as np
import pickle
import sys
import io

MAGIC_PREFIX = b'\x93NUMPY'
MAGIC_LEN = len(MAGIC_PREFIX) + 2

def _read_bytes(fp, size, error_template="ran out of data"):
    """
    Read from file-like object until size bytes are read.
    Raises ValueError if not EOF is encountered before size bytes are read.
    Non-blocking objects only supported if they derive from io objects.
    Required as e.g. ZipExtFile in python 2.6 can return less data than
    requested.
    """
    data = bytes()
    while True:
        # io files (default in python3) return None or raise on
        # would-block, python2 file will truncate, probably nothing can be
        # done about that.  note that regular files can't be non-blocking
        try:
            r = fp.read(size - len(data))
            data += r
            if len(r) == 0 or len(data) == size:
                break
        except io.BlockingIOError:
            pass
    if len(data) != size:
        msg = "EOF: reading %s, expected %d bytes got %d"
        raise ValueError(msg % (error_template, size, len(data)))
    else:
        return data

def read_magic(fp):
    """ Read the magic string to get the version of the file format.
    Parameters
    ----------
    fp : filelike object
    Returns
    -------
    major : int
    minor : int
    """
    magic_str = _read_bytes(fp, MAGIC_LEN, "magic string")
    if magic_str[:-2] != MAGIC_PREFIX:
        msg = "the magic string is not correct; expected %r, got %r"
        raise ValueError(msg % (MAGIC_PREFIX, magic_str[:-2]))
    if sys.version_info[0] < 3:
        major, minor = map(ord, magic_str[-2:])
    else:
        major, minor = magic_str[-2:]
    return major, minor

def _filter_header(s):
    """Clean up 'L' in npz header ints.
    Cleans up the 'L' in strings representing integers. Needed to allow npz
    headers produced in Python2 to be read in Python3.
    Parameters
    ----------
    s : byte string
        Npy file header.
    Returns
    -------
    header : str
        Cleaned up header.
    """
    import tokenize
    if sys.version_info[0] >= 3:
        from io import StringIO
    else:
        from StringIO import StringIO

    tokens = []
    last_token_was_number = False
    # adding newline as python 2.7.5 workaround
    string = asstr(s) + "\n"
    for token in tokenize.generate_tokens(StringIO(string).readline):
        token_type = token[0]
        token_string = token[1]
        if (last_token_was_number and
                token_type == tokenize.NAME and
                token_string == "L"):
            continue
        else:
            tokens.append(token)
        last_token_was_number = (token_type == tokenize.NUMBER)
    # removing newline (see above) as python 2.7.5 workaround
    return tokenize.untokenize(tokens)[:-1]

def _read_array_header(fp, version):
    """
    see read_array_header_1_0
    """
    # Read an unsigned, little-endian short int which has the length of the
    # header.
    import struct
    if version == (1, 0):
        hlength_type = '<H'
    elif version == (2, 0):
        hlength_type = '<I'
    else:
        raise ValueError("Invalid version %r" % version)

    hlength_str = _read_bytes(fp, struct.calcsize(hlength_type), "array header length")
    header_length = struct.unpack(hlength_type, hlength_str)[0]
    header = _read_bytes(fp, header_length, "array header")

    # The header is a pretty-printed string representation of a literal
    # Python dictionary with trailing newlines padded to a ARRAY_ALIGN byte
    # boundary. The keys are strings.
    #   "shape" : tuple of int
    #   "fortran_order" : bool
    #   "descr" : dtype.descr
    header = _filter_header(header)
    try:
        d = safe_eval(header)
    except SyntaxError as e:
        msg = "Cannot parse header: %r\nException: %r"
        raise ValueError(msg % (header, e))
    if not isinstance(d, dict):
        msg = "Header is not a dictionary: %r"
        raise ValueError(msg % d)
    keys = sorted(d.keys())
    if keys != ['descr', 'fortran_order', 'shape']:
        msg = "Header does not contain the correct keys: %r"
        raise ValueError(msg % (keys,))

    # Sanity-check the values.
    if (not isinstance(d['shape'], tuple) or
            not numpy.all([isinstance(x, (int, long)) for x in d['shape']])):
        msg = "shape is not valid: %r"
        raise ValueError(msg % (d['shape'],))
    if not isinstance(d['fortran_order'], bool):
        msg = "fortran_order is not a valid bool: %r"
        raise ValueError(msg % (d['fortran_order'],))
    try:
        dtype = numpy.dtype(d['descr'])
    except TypeError as e:
        msg = "descr is not a valid dtype descriptor: %r"
        raise ValueError(msg % (d['descr'],))

    return d['shape'], d['fortran_order'], dtype

filename = 'X:/test/shapes.npy'
fp = open(filename, 'rb')
version = read_magic(fp)
shape, fortran_order, dtype = _read_array_header(fp, version)

print('version: ',version)

sys.exit()

data = np.load('x:/test/shapes.npy').item()
dataShapes = data['shapes']

activeXY = []
activeXYFrames = []
for xy in range(dataShapes.shape[0]):
    if np.any(dataShapes[xy]>0):
        activeXY.append(xy)
        activeFrames = 0
        for t in range(len(dataShapes[xy])):
            if len(dataShapes[xy][t])>0:
                activeFrames += 1
        activeXYFrames.append(activeFrames)
activeXY = np.unique(activeXY)

print('activeXY: ',activeXY)
print('activeXYFrames: ',activeXYFrames)