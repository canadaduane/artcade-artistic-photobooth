import Tkinter
from PIL import Image, ImageTk
import time
import cv2

class mainWindow():
  times=1
  timestart=time.clock()
  
  def __init__(self):
    self.root = Tkinter.Tk()
    self.root.attributes("-fullscreen", True)

    self.capture = cv2.VideoCapture(0)
    self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 800)
    self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 600)

    self.frame = Tkinter.Frame(self.root, width=800, height=600)
    self.frame.pack()
    self.canvas = Tkinter.Canvas(self.frame, width=800,height=600)
    self.canvas.place(x=-2,y=-2)
    self.root.after(0,self.start) # INCREASE THE 0 TO SLOW IT DOWN

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

  def capture_to_image(self, frame):
    cv2img = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGBA)
    return ImageTk.PhotoImage(Image.fromarray(cv2img))

  def start(self):
    err, frame = self.capture.read()
    if frame is not None:
      self.im = self.capture_to_image(frame)
      self.canvas.create_image(0,0,image=self.im,anchor=Tkinter.NW)
      self.root.update()
      self.times+=1
      if self.times%33==0:
              print "%.02f FPS"%(self.times/(time.clock()-self.timestart))
      self.root.after(10,self.start)

if __name__ == '__main__':
    x=mainWindow()
