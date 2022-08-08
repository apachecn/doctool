import av
import av.datasets
import os
import cv2
import argparse
import shutil
import math
import sys

def ext(fname, videos_save_path):
    img_path = os.path.join(videos_save_path, os.path.basename(fname) + '_img')
    print(img_path)
    if os.path.isdir(img_path):
        shutil.rmtree(img_path)
    os.mkdir(img_path)
    container = av.open(fname)

    stream = container.streams.video[0]
    stream.codec_context.skip_frame = 'NONKEY'

    for frame in container.decode(stream):

        frame.to_image().save(img_path + '/' + 'night-sky.{:04d}.jpg'.format(frame.pts), quality=80)


fname = sys.argv[1]
videos_save_path = 'out'
if not os.path.exists(videos_save_path):
    os.makedirs(videos_save_path)
print(fname)
ext(fname, videos_save_path)

