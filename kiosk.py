from Tkinter import *
from PIL import Image, ImageTk
from datetime import datetime
import time
import cv2
import os
import errno   
from re import match, sub
from math import sin, cos, pi
from colour import Color
from glob import glob

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
    iter_m = match(r"""^Iteration: (\d+), cost: (.+)$""", line)
    status_m = match(r"""^Status: (.+)$""", line)
    if iter_m:
      return (int(iter_m.group(1)) + 1, float(iter_m.group(2)))
    elif status_m:
      if status_m.group(1) == "starting":
        return (1, 0.0)
      elif status_m.group(1) == "done":
        # We use maxIterations+1 as a sentinel value indicating "completely done"
        # without this, it's possible the neural_artistic_style.py script can
        # report its last iteration, meanwhile the output.jpg file has not been
        # written to disk (or is partially written to disk)
        return (ArtRequest.maxIterations + 1, 0.0)
      else:
        return (None, None)
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

  def is_done(self):
    status = self.get_status()
    if status:
      return status >= ArtRequest.maxIterations+1
    else:
      return False

  def save(self):
    # We need the initial directory to be in the "prepare" state so
    # that the runner doesn't grab the request while we're still load-
    # ing the directory with images to be processed.
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
  wheel_inner_radius = 50
  wheel_outer_radius = 150

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

    self.available_art = self.get_available_art()

    self.root.mainloop()

  def click_callback(self, event):
    print "clicked at: ", event.x, "and: ", event.y

  def key_callback(self, event):
    key = event.keysym.lower()
    print "key: ", key

    # reset triple-backspace keypress counter if not backspace
    if key != "backspace":
      self.backspace_count = 0

    if key == "escape":
      self.root.quit()
    elif key == "left":
      self.capture_target = "style"
      self.active_req = None
      self.cycle_art(-1)
      self.draw_art_number()
    elif key == "right":
      self.capture_target = "style"
      self.active_req = None
      self.cycle_art(1)
      self.draw_art_number()
    elif key == "space":
      # Toggle capture window between style and subject
      if self.capture_target == "style":
        self.last_style_image = self.image
        self.photo = ImageTk.PhotoImage(self.last_style_image)
        self.last_style_photo = self.photo
        self.capture_target = "subject"
      elif self.capture_target == "subject":
        self.last_subject_image = self.image.transpose(Image.FLIP_LEFT_RIGHT)
        self.photo = ImageTk.PhotoImage(self.last_subject_image)
        self.last_subject_photo = self.photo
        self.capture_target = "result"
        self.make_art_request()
        self.draw_waiting()
      elif self.capture_target == "result":
        if self.active_req is None or self.active_req.is_done():
          # Back to the beginning state
          self.reset()
          self.erase()
          print "Reset!"
        else:
          print "Ignoring reset (not done processing active request)"
      # Whenever state changes, "freeze" the last frame
      self.show_last_images()
    elif key == "backspace":
      if self.art_path:
        self.backspace_count += 1
        if self.backspace_count >= 3:
          self.backspace_count = 0
          self.delete_selected_art()
          self.capture_target = "result"
          self.active_req = None
          self.cycle_art(0)

  def reset(self):
    self.capture_target = "style"
    self.image = None
    self.photo = None
    self.last_style_image = None
    self.last_subject_image = None
    self.active_req = None
    self.art_index = -1
    self.art_path = None
    self.backspace_count = 0
    self.wheel_extender_size = 0

  def erase(self):
    self.canvas_style.delete(ALL)
    self.canvas_subject.delete(ALL)
    self.canvas_result.delete(ALL)

  def delete_selected_art(self):
    """Marks the art folder as deleted"""
    if self.art_path and os.path.isdir(self.art_path):
      deleted_path_name = sub(r'\.[^\.]+$', '.deleted', self.art_path)
      os.rename(self.art_path, deleted_path_name)
      del self.available_art[self.art_index]
      return True
    else:
      return False

  def center_image_on_canvas(self, image, canvas, photo = None):
    width, height = image.size
    window_width = canvas.winfo_width()
    window_height = canvas.winfo_height()

    if width > window_width or height > window_height:
      image.thumbnail((window_width, window_height), Image.ANTIALIAS)
      width, height = image.size

    if photo is None:
      photo = ImageTk.PhotoImage(image)

    x = window_width / 2 - width / 2
    y = window_height / 2 - height / 2
    canvas.create_image(x, y, image=photo, anchor=NW)

    return photo

  def get_art_paths(self, root_path):
    return (
      os.path.join(root_path, "style.jpg"),
      os.path.join(root_path, "subject.jpg"),
      os.path.join(root_path, "output.jpg")
      )

  def get_available_art(self):
    search_path = os.path.join(cwd(), "images", "*.processing")
    print "Getting available art at ", search_path
    paths = list(sorted(glob(search_path)))
    available = []
    count = 0
    for path in paths:
      p1, p2, p3 = self.get_art_paths(path)
      if os.path.isfile(p1) and \
         os.path.isfile(p2) and \
         os.path.isfile(p3):
        available.append(path)
      count += 1
      if (count % 10 == 0):
        print "  loaded ", count, " images"
    return available

  def show_art(self, art_path):
    if art_path:
      self.erase()
      style_path, subject_path, output_path = self.get_art_paths(art_path)

      self.image = Image.open(style_path)
      self.photo = self.center_image_on_canvas(self.image, self.canvas_style)
      self.last_style_image = self.image
      self.last_style_photo = self.photo

      self.extra_image = Image.open(subject_path)
      self.photo = self.center_image_on_canvas(self.extra_image, self.canvas_subject)
      self.last_subject_image = self.extra_image
      self.last_subject_photo = self.photo

      self.extra_image = Image.open(output_path)
      self.photo = self.center_image_on_canvas(self.extra_image, self.canvas_result)
      self.last_result_image = self.extra_image
      self.last_result_photo = self.photo


  def cycle_art(self, direction = 1):
    self.art_index += direction

    if (self.art_index < -1):
      self.art_index = len(self.available_art) - 1
    if (self.art_index >= len(self.available_art)):
      self.art_index = -1

    if self.art_index == -1:
        # Back to the beginning state
        self.reset()
        self.erase()
        print "Reset! (cycle)"
    else:
      self.art_path = self.available_art[self.art_index]
      print "art_index: ", self.art_index
      print "art_path: ", self.art_path
      self.show_art(self.art_path)

  def choose_capture_canvas(self):
    if self.capture_target == "style" and not self.art_path:
      return self.canvas_style
    elif self.capture_target == "subject":
      return self.canvas_subject
    else:
      return None

  def show_last_images(self):
    if (self.last_style_image is not None and self.capture_target != "style"):
      self.canvas_style.delete(ALL)
      self.center_image_on_canvas(self.last_style_image, self.canvas_style, self.last_style_photo)
    
    if (self.last_subject_image is not None and self.capture_target != "subject"):
      self.canvas_subject.delete(ALL)
      self.center_image_on_canvas(self.last_subject_image, self.canvas_subject, self.last_subject_photo)

  def make_art_request(self):
    self.active_req = ArtRequest(style=self.last_style_image, subject=self.last_subject_image)
    print "ArtRequest ID: ", self.active_req.uid
    self.active_req.save()
    self.art_path = None

  def draw_result(self):
    self.canvas_result.delete(ALL)
    self.result_image = Image.open(self.active_req.output_filepath())
    self.result_photo = self.center_image_on_canvas(self.result_image, self.canvas_result)

  def draw_painting_message(self):
    x = self.scrw/2
    y = self.scrh
    self.canvas_result.create_text(x + 10, y + MainWindow.wheel_outer_radius + 30,
      text="Painting...", fill="white", font=("Droid Serif", 32))

  def draw_art_number(self, number=None):
    x = 0
    y = 0
    if number == None:
      number = self.art_index
    if number >= 0:
      self.canvas_result.create_text(x + 100, y + 30,
        text="Paiting #" + str(number+1), fill="#CCC", font=("Droid Serif", 24))

  def draw_waiting(self):
    self.canvas_result.delete(ALL)
    self.draw_painting_message()

  def draw_percent_complete(self, percent, first_tick_percent=2.0):
    self.canvas_result.delete(ALL)
    x = self.scrw/2
    y = self.scrh
    c = Color("blue")
    inr = MainWindow.wheel_inner_radius

    # Extend the first "spoke" in the wheel as we wait for actual status data
    if percent <= first_tick_percent and self.wheel_extender_size < (MainWindow.wheel_outer_radius - inr):
      outr = inr + self.wheel_extender_size
    else:
      outr = MainWindow.wheel_outer_radius

    for i in range(int(percent)):
      radians = float(i) * pi * 2 / 100.0
      # dark "anti-aliasing" line
      d = Color(hue = c.hue, saturation = c.saturation, luminance = c.luminance * 0.55)
      self.canvas_result.create_line(
        x + cos(radians)*(inr-4),
        y + sin(radians)*(inr-4),
        x + cos(radians)*(outr+2),
        y + sin(radians)*(outr+2),
        fill=d.hex, width=3.0, smooth=1)
      # regular line
      self.canvas_result.create_line(
        x + cos(radians)*inr,
        y + sin(radians)*inr,
        x + cos(radians)*outr,
        y + sin(radians)*outr,
        fill=c.hex, width=2.0, smooth=1)
      c.hue += 0.01
    self.draw_painting_message()

  def check_status(self):
    if self.active_req:
      status = self.active_req.get_status()
      if status:
        print "Status of {0}: {1}".format(self.active_req.uid, status)
        if self.active_req.is_done():
          self.draw_result()
        else:
          percent = float(status) * 100 / ArtRequest.maxIterations + 1
          self.wheel_extender_size += 2
          self.draw_percent_complete(percent)
      else:
        print "Status of {0} unavailable".format(self.active_req.uid)

    # Schedule the next status check
    self.root.after(100, self.check_status)

  def capture_to_image(self, frame):
    """Convert an OpenCV camera frame to a PhotoImage, flipping horizontally"""
    cv2img = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGBA)
    return Image.fromarray(cv2img)

  def stream_camera(self):
    """Endless loop that grabs camera frames and sends them to the active canvas"""
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
