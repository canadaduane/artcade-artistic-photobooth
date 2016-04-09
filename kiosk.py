from Tkinter import *
from PIL import Image, ImageTk
from datetime import datetime
import time
import cv2
import os
import errno   
from re import match
from math import sin, cos, pi
from colour import Color

def cwd():
  return os.path.dirname(os.path.realpath(__file__))

class ArtRequest():
  maxIterations = 200

  def __init__(self, style=None, subject=None):
    self.style = style
    self.subject = subject
    self.uid = self.unique_id()

  def unique_id(self):
    dt = datetime.now()
    uid = dt.strftime("%Y-%m-%d.%H-%M-%S")
    return "{0}.{1}".format(uid, (dt.microsecond / 10000))

  def image_dir(self):
    return os.path.join(cwd(), 'images')

  def request_dir(self, suffix="request"):
    return os.path.join(self.image_dir(), self.uid) + "." + suffix

  def output_filepath(self):
    path = os.path.join(self.request_dir("processing"), "output.jpg")
    return path

  def status_filepath(self):
    path = os.path.join(self.request_dir("processing"), "stdout.txt")
    return path

  def is_stdout_available(self):
    available = os.path.isfile(self.status_filepath())
    return available

  def mkdir_p(self, path):
    try:
      os.makedirs(path)
    except OSError as exc:  # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(path):
        pass
      else:
        raise

  def tail(self, f, n=1):
    stdin, stdout = os.popen2("tail -n {0} {1}".format(n, f))
    stdin.close()
    lines = stdout.readlines(); stdout.close()
    return lines[-n:]

  def parse_status_line(self, line):
    m = match(r"""^Iteration: (\d+), cost: (.+)$""", line)
    if m:
      return (int(m.group(1)), float(m.group(2)))
    else:
      return (None, None)

  def get_status(self):
    if self.is_stdout_available():
      lines = self.tail(self.status_filepath())
      if len(lines) > 0:
        iteration, cost = self.parse_status_line(lines[0])
        return iteration
      else:
        print "Can't tail ", self.status_filepath()
        return None
    else:
      return None

  def save(self):
    path = self.request_dir("prepare")
    print "Creating dir: ", path
    self.mkdir_p(path)
    self.style.save(os.path.join(path, "style.jpg"))
    self.subject.save(os.path.join(path, "subject.jpg"))
    # change from "*.prepare" to "*.request"
    os.rename(path, self.request_dir())


class MainWindow():
  times=1
  timestart=time.clock()
  
  def __init__(self):
    self.reset()

    self.root = Tk()
    self.root.attributes("-fullscreen", True)
    # self.root.pack(expand=1)

    label_width = 180

    self.scrw = self.root.winfo_screenwidth() / 2
    self.scrh = self.root.winfo_screenheight() / 2
    self.capw = 640
    self.caph = 480
    self.margin_left = (self.scrw - self.capw) / 2 - label_width / 2
    self.margin_top = (self.scrh - self.caph) / 2

    print "Screen (half)size: {0}x{1}".format(self.scrw, self.scrh)
    print "Capture size: {0}x{1}".format(self.capw, self.caph)

    self.capture = cv2.VideoCapture(0)
    self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.capw)
    self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.caph)

    self.capture_target = 'style'

    self.root.columnconfigure(0, weight=0)
    self.root.columnconfigure(1, weight=0)
    self.root.columnconfigure(2, weight=1)
    self.root.rowconfigure(0, weight=1)
    self.root.rowconfigure(1, weight=1)

    f_a = Frame(self.root, bd=0)
    f_a.grid(row=0, column=0)
    self.canvas_style_label = Canvas(f_a, width=label_width, height=self.scrh, bg="white", highlightthickness=0)
    self.canvas_style_label.pack()
    image = Image.open(os.path.join(cwd(), "assets", "style_label.jpg"))
    self.style_label_photo = ImageTk.PhotoImage(image)
    self.canvas_style_label.create_image(0, 0, image=self.style_label_photo, anchor=NW)

    f_b = Frame(self.root, bd=0)
    f_b.grid(row=1, column=0)
    self.canvas_subject_label = Canvas(f_b, width=label_width, height=self.scrh, bg="white", highlightthickness=0)
    self.canvas_subject_label.pack()
    image = Image.open(os.path.join(cwd(), "assets", "subject_label.jpg"))
    self.subject_label_photo = ImageTk.PhotoImage(image)
    self.canvas_subject_label.create_image(0, 0, image=self.subject_label_photo, anchor=NW)

    f1 = Frame(self.root, bd=0)
    f1.grid(row=0, column=1)

    self.canvas_style = Canvas(f1, width=self.scrw-label_width, height=self.scrh, bg="#333", highlightthickness=0)
    self.canvas_style.pack()

    f2 = Frame(self.root)
    f2.grid(row=1, column=1)

    self.canvas_subject = Canvas(f2, width=self.scrw-label_width, height=self.scrh, bg="#555", highlightthickness=0)
    self.canvas_subject.pack()

    f3 = Frame(self.root)
    f3.grid(row=0, column=2, rowspan=2, sticky=N+S+E+W)

    self.canvas_result = Canvas(f3, width=self.scrw, height=self.scrh, bg="black", highlightthickness=0)
    self.canvas_result.pack(fill=BOTH, expand=1)

    self.root.after(0, self.stream_camera)
    self.root.after(500, self.check_status)
    self.root.bind("<Key>", self.key_callback)
    self.root.bind("<Button-1>", self.click_callback)

    self.root.mainloop()

  def click_callback(self, event):
    print "clicked at: ", event.x, "and: ", event.y

  def key_callback(self, event):
    key = event.keysym.lower()
    print "key: ", key
    if key == "escape":
      self.root.quit()
    elif key == "s":
      self.cycle_canned_styles()
    elif key == "space":
      # Toggle capture window between style and subject
      if self.capture_target == "style":
        self.last_style_image = self.image
        self.last_style_photo = self.photo
        self.capture_target = "subject"
      elif self.capture_target == "subject":
        self.last_subject_image = self.image
        self.last_subject_photo = self.photo
        self.capture_target = "result"
        self.make_art_request()
        self.draw_waiting()
      elif self.capture_target == "result":
        # Back to the beginning state
        self.capture_target = "style"
        self.reset()
        self.erase()

      # Whenever state changes, "freeze" the last frame
      self.show_last_images()

  def reset(self):
    self.image = None
    self.photo = None
    self.last_style_image = None
    self.last_subject_image = None
    self.active_req = None
    self.canned_index = 0

  def erase(self):
    #self.canvas_style.delete(ALL)
    self.canvas_subject.delete(ALL)
    self.canvas_result.delete(ALL)

  def cycle_canned_styles(self):
    self.canned_index += 1
    path = os.path.join(cwd(), "assets", "style-{0:02}.jpg".format(self.canned_index))
    print "Using canned style: ", path
    if os.path.isfile(path):
      self.image = Image.open(path)
      self.last_style_image = self.image
      self.photo = ImageTk.PhotoImage(self.image)
      self.last_style_photo = self.photo

      # margin_left =
      self.canvas_style.create_image(self.margin_left, self.margin_top, image=self.photo, anchor=NW)
    else:
      self.canned_index = 0

  def capture_to_image(self, frame):
    """Convert an OpenCV camera frame to a PhotoImage"""
    cv2img = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGBA)
    return Image.fromarray(cv2img)

  def choose_capture_canvas(self):
    if self.capture_target == "style" and self.canned_index == 0:
      return self.canvas_style
    elif self.capture_target == "subject":
      return self.canvas_subject
    else:
      return None

  def show_last_images(self):
    if (self.last_style_image is not None and self.capture_target != "style"):
      self.canvas_style.delete(ALL)
      self.canvas_style.create_image(self.margin_left, self.margin_top, image=self.last_style_photo, anchor=NW)
    
    if (self.last_subject_image is not None and self.capture_target != "subject"):
      self.canvas_subject.delete(ALL)
      self.canvas_subject.create_image(self.margin_left, self.margin_top, image=self.last_subject_photo, anchor=NW)

  def make_art_request(self):
    self.active_req = ArtRequest(style=self.last_style_image, subject=self.last_subject_image)
    print "ArtRequest ID: ", self.active_req.uid
    self.active_req.save()

  def draw_result(self):
    self.result_image = Image.open(self.active_req.output_filepath())
    self.result_photo = ImageTk.PhotoImage(self.result_image)
    self.canvas_result.delete(ALL)
    width, height = self.result_image.size
    x = self.canvas_result.winfo_width() / 2 - width / 2
    y = self.margin_top + self.scrh/2
    self.canvas_result.create_image(x, y, image=self.result_photo, anchor=NW)

  def draw_waiting(self):
    x = self.scrw/2
    y = self.scrh
    self.canvas_result.delete(ALL)
    self.canvas_result.create_text(x, y, text="Painting...", fill="white", font=("Droid Serif", 32))

  def draw_percent_complete(self, percent):
    self.canvas_result.delete(ALL)
    inner_radius = 50
    outer_radius = 150
    x = self.scrw/2
    y = self.scrh
    c = Color("blue")
    for i in range(int(percent)):
      radians = float(i) * pi * 2 / 100.0
      # dark "anti-aliasing" line
      d = Color(hue = c.hue, saturation = c.saturation, luminance = c.luminance * 0.55)
      self.canvas_result.create_line(
        x + cos(radians)*(inner_radius-4), y + sin(radians)*(inner_radius-4),
        x + cos(radians)*(outer_radius+2), y + sin(radians)*(outer_radius+2),
        fill=d.hex, width=3.0, smooth=1)
      # regular line
      self.canvas_result.create_line(
        x + cos(radians)*inner_radius, y + sin(radians)*inner_radius,
        x + cos(radians)*outer_radius, y + sin(radians)*outer_radius,
        fill=c.hex, width=2.0, smooth=1)
      c.hue += 0.01

    self.canvas_result.create_text(x + 10, y + outer_radius + 30, text="Painting...", fill="white", font=("Droid Serif", 32))

  def check_status(self):
    if self.active_req:
      status = self.active_req.get_status()
      if status:
        print "Status of {0}: {1}".format(self.active_req.uid, status)
        if status < ArtRequest.maxIterations-1:
          percent = float(status) * 100 / ArtRequest.maxIterations + 1
          self.draw_percent_complete(percent)
        if status == ArtRequest.maxIterations-1:
          self.draw_result()
      else:
        print "Status of {0} unavailable".format(self.active_req.uid)

    # Schedule the next status check
    self.root.after(500, self.check_status)

  def stream_camera(self):
    canvas = self.choose_capture_canvas()
    if canvas:
      canvas.delete(ALL)

      err, frame = self.capture.read()
      if frame is not None:
        self.image = self.capture_to_image(frame)
        self.photo = ImageTk.PhotoImage(self.image)

        # show camera grab frame on active canvas
        canvas.create_image(self.margin_left, self.margin_top, image=self.photo, anchor=NW)

        # redraw
        self.root.update()

        self.times += 1
        if self.times%33==0:
          fps = self.times / (time.clock() - self.timestart)
          print "{0}: {1} FPS".format(time.clock(), fps)

    # Schedule the next camera frame grab
    self.root.after(10, self.stream_camera)

if __name__ == '__main__':
  MainWindow()
