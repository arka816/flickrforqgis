'''
    s	thumbnail	75	cropped square
    q	thumbnail	150	cropped square
    t	thumbnail	100	
    m	small	240	
    n	small	320	
    w	small	400	
    (none)	medium	500	
    z	medium	640	
    c	medium	800	
    b	large	1024	
    h	large	1600	has a unique secret; photo owner can restrict
    k	large	2048	has a unique secret; photo owner can restrict
    3k	extra large	3072	has a unique secret; photo owner can restrict
    4k	extra large	4096	has a unique secret; photo owner can restrict
    f	extra large	4096	has a unique secret; photo owner can restrict; only exists for 2:1 aspect ratio photos
    5k	extra large	5120	has a unique secret; photo owner can restrict
    6k	extra large	6144	has a unique secret; photo owner can restrict
    o	original	arbitrary	has a unique secret; photo owner can restrict; files have full EXIF data; files might not be rotated; files can use an arbitrary file extension
'''

IMAGE_SIZE_SUFFIX_MAP = {
    '_s': 75,
    '_q': 150,
    '_t': 100,
    '_m': 240,
    '_n': 320,
    '_w': 400,
    '' : 500,
    '_z': 640,
    '_c': 800,
    '_b': 1024,
    '_h': 1600,
    '_k': 2048,
    '_3k': 3072,
    '_4k': 4096,
    '_f': 4096,
    '_5k': 5120,
    '_6k': 6144
}

IMAGE_SIZE_SUFFIX_MAP_INV = {val: key for key, val in IMAGE_SIZE_SUFFIX_MAP.items()}

IMAGE_SIZE = 500
IMAGE_SIZE_SUFFIX = IMAGE_SIZE_SUFFIX_MAP_INV[IMAGE_SIZE]
IMAGE_URL_TYPE = 'url' + IMAGE_SIZE_SUFFIX

LOCATION_ACCURACY = 16
RES_PER_PAGE = 250          # defaults to 100; maximum is 500
MAX_RES_PER_QUERY = 4000    # flickr API business policy
MAX_SAME_QUERIES = MAX_RES_PER_QUERY / RES_PER_PAGE
# assuming flickr does not have a data density that would gives us more 
# than 4000 entries withing a box subtending 1e-4 latitudes and longitudes
BOX_DIVISION_THRESHOLD = 1e-4   

CHUNK_SIZE = 4096
