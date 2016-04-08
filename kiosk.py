from Tkinter import *

root = Tk()

root.attributes("-fullscreen", True)

root.bind_all("q", lambda e: e.widget.quit())


def click_callback(event):
    print "clicked at: ", event.x, "and: ", event.y

root.bind("<Button-1>", click_callback)

def key_callback(event):
    key = event.keysym.lower()
    print "key: ", key
    if key == "escape":
        root.quit()

root.bind("<Key>", key_callback)

w = Label(root, text="Hello, world!")
w.pack()

root.mainloop()
