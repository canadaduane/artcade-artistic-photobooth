from Tkinter import *
from PIL import Image, ImageTk
from datetime import datetime
import time
import cv2
import os
import errno   

class ArtRequest():

  def __init__(self, style=None, subject=None):
    self.style = style
    self.subject = subject
    self.uid = self.unique_id()

  def unique_id(self):
    dt = datetime.now()
    uid = dt.strftime("%Y-%m-%d.%H-%M-%S")
    return "{0}.{1}".format(uid, (dt.microsecond / 10000))

  def cwd(self):
    return os.path.dirname(os.path.realpath(__file__))

  def image_dir(self):
    return os.path.join(self.cwd(), 'images')

  def request_dir(self):
    return os.path.join(self.image_dir(), self.uid) + ".request"

  def mkdir_p(self, path):
    try:
      os.makedirs(path)
    except OSError as exc:  # Python >2.5
      if exc.errno == errno.EEXIST and os.path.isdir(path):
        pass
      else:
        raise

  def save(self):
    path = self.request_dir()
    print "Creating dir: ", path
    self.mkdir_p(path)
    self.style.save(os.path.join(path, "style.jpg"))
    self.subject.save(os.path.join(path, "subject.jpg"))


class MainWindow():
  times=1
  timestart=time.clock()
  
  def __init__(self):
    self.last_style_image = None
    self.last_subject_image = None

    self.root = Tk()
    self.root.attributes("-fullscreen", True)
    # self.root.pack(expand=1)

    self.scrw = self.root.winfo_screenwidth() / 2
    self.scrh = self.root.winfo_screenheight() / 2
    self.capw = 640
    self.caph = 480
    self.margin_left = (self.scrw - self.capw) / 2
    self.margin_top = (self.scrh - self.caph) / 2

    print "Screen (half)size: {0}x{1}".format(self.scrw, self.scrh)
    print "Capture size: {0}x{1}".format(self.capw, self.caph)

    self.capture = cv2.VideoCapture(0)
    self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.capw)
    self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.caph)

    self.capture_target = 'style'

    self.root.columnconfigure(0, weight=0)
    self.root.columnconfigure(1, weight=1)
    self.root.rowconfigure(0, weight=1)
    self.root.rowconfigure(1, weight=1)

    f1 = Frame(self.root, bd=0)
    f1.grid(row=0, column=0)

    self.canvas_style = Canvas(f1, width=self.scrw, height=self.scrh, bg="black", highlightthickness=0)
    self.canvas_style.pack()

    f2 = Frame(self.root)
    f2.grid(row=1, column=0)

    self.canvas_subject = Canvas(f2, width=self.scrw, height=self.scrh, bg="black", highlightthickness=0)
    self.canvas_subject.pack()

    f3 = Frame(self.root)
    f3.grid(row=0, column=1, rowspan=2, sticky=N+S+E+W)

    self.canvas_result = Canvas(f3, width=self.scrw, height=self.scrh, bg="black")
    self.canvas_result.pack(fill=BOTH, expand=1)

    self.root.after(0, self.start)
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
      elif self.capture_target == "result":
        self.capture_target = "style"

      # Whenever state changes, "freeze" the last frame
      self.show_last_images()

  def capture_to_image(self, frame):
    """Convert an OpenCV camera frame to a PhotoImage"""
    cv2img = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGBA)
    return Image.fromarray(cv2img)

  def choose_capture_canvas(self):
    if self.capture_target == "style":
      return self.canvas_style
    elif self.capture_target == "subject":
      return self.canvas_subject
    elif self.capture_target == "result":
      return self.canvas_result
    else:
      raise Exception("Capture Target in unknown state: {0}".format(self.capture_target))

  def show_last_images(self):
    if (self.last_style_image is not None and self.capture_target != "style"):
      self.canvas_style.delete(ALL)
      self.canvas_style.create_image(self.margin_left, self.margin_top, image=self.last_style_photo, anchor=NW)
    
    if (self.last_subject_image is not None and self.capture_target != "subject"):
      self.canvas_subject.delete(ALL)
      self.canvas_subject.create_image(self.margin_left, self.margin_top, image=self.last_subject_photo, anchor=NW)

  def make_art_request(self):
    req = ArtRequest(style=self.last_style_image, subject=self.last_subject_image)
    print "ArtRequest ID: ", req.uid
    req.save()

  def start(self):
    err, frame = self.capture.read()
    if frame is not None:
      self.image = self.capture_to_image(frame)
      self.photo = ImageTk.PhotoImage(self.image)

      canvas = self.choose_capture_canvas()
      canvas.delete(ALL)
      canvas.create_image(self.margin_left, self.margin_top, image=self.photo, anchor=NW)
      self.root.update()

      self.times += 1
      if self.times%33==0:
        fps = self.times / (time.clock() - self.timestart)
        print "{0}: {1} FPS".format(time.clock(), fps)

      # Schedule the next camera frame grab
      self.root.after(10, self.start)

if __name__ == '__main__':
  MainWindow()
