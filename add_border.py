#! /usr/bin/python3

'''
example: ./add_border.py source/images/use-rxjs-to-handle-data-flows
'''

import sys
import os
from PIL import Image, ImageOps
import glob

def run():
  for filename in glob.glob(sys.argv[1] + '/*.png'):
    directory = './' + filename.split('/')[-2]
    name = filename.split('/')[-1]
    img = Image.open(filename)
    img_with_border = ImageOps.expand(img, border=1, fill='#bcbcbc')
    if not os.path.exists(directory):
      os.makedirs(directory)
    img_with_border.save(directory + '/' + name)


if __name__ == "__main__":
  if len(sys.argv) < 2:
    raise Exception('参数不够')
  print(f"Arguments count: {len(sys.argv)}")
  for i, arg in enumerate(sys.argv):
    print(f"Argument {i:>6}: {arg}")
  run()
