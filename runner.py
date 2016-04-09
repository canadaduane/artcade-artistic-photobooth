from glob import glob
from time import sleep
from os import path, rename
from re import sub
from sys import stdout
from subprocess import call

def newstate(filepath, state):
  return sub(r'\.[^\.]+$', '.' + state, filepath)

def process(filepath):
  processing = newstate(filepath, "processing")
  rename(filepath, processing)

  style_path = path.join(processing, "style.jpg")
  subject_path = path.join(processing, "subject.jpg")
  output_path = path.join(processing, "output.jpg")
  stdout_path = path.join(processing, "stdout.txt")

  cmd = "python -u /style/neural_artistic_style.py " \
    "--style {0} --subject {1} --output {2} " \
    "--network /style/imagenet-vgg-verydeep-19.mat " \
    "".format(style_path, subject_path, output_path)
  with open(stdout_path, 'w') as f:
    call(cmd.split(), stdout=f, bufsize=1)

count = 0
while(True):
  print "Checking for requests... ", count
  count += 1
  stdout.flush()
  files = glob("images/*.request")
  for file in files:
    print "request: ", path.basename(file)
    stdout.flush()
  if len(files) > 0:
    print "* Processing: ", files[0]
    stdout.flush()
    process(files[0])
  sleep(1)
  
  print
  stdout.flush()