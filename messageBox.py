# -*- coding: utf-8 -*-
"""
Created on Sat Apr 14 22:59:03 2018

@author: Edward
"""

from __future__ import print_function

import tkinter as tkinter
import os
import sys
from commonFunctions import findFilenameFromFolder
import numpy as np

class MessageBox(object):

    def __init__(self, msg, b1, b2, frame, t, entry, width=None, text=None):

        root = self.root = tkinter.Tk()
        root.title('Message')
        self.msg = str(msg)
        # ctrl+c to copy self.msg
        root.bind('<Control-c>', func=self.to_clip)
        # remove the outer frame if frame=False
        if not frame: root.overrideredirect(True)
        # default values for the buttons to return
        self.b1_return = True
        self.b2_return = False
        # if b1 or b2 is a tuple unpack into the button text & return value
        if isinstance(b1, tuple): b1, self.b1_return = b1
        if isinstance(b2, tuple): b2, self.b2_return = b2
        # main frame
        frm_1 = tkinter.Frame(root)
        frm_1.pack(ipadx=2, ipady=2)
        # the message
        message = tkinter.Label(frm_1, text=self.msg)
        message.pack(padx=8, pady=8)
        # if entry=True create and set focus
        if entry:
            self.entry = tkinter.Entry(frm_1,width=width)
            #self.entry.setvar(text);
            #self.entry.insert(tkinter.END, 'default text')
            #self.entry.config(width=20)
            #self.entry.place(width=100)            
            self.entry.pack()
            self.entry.focus_set()
        # button frame
        frm_2 = tkinter.Frame(frm_1)
        frm_2.pack(padx=4, pady=4)
        # buttons
        btn_1 = tkinter.Button(frm_2, width=8, text=b1)
        btn_1['command'] = self.b1_action
        btn_1.pack(side='left')
        if not entry: btn_1.focus_set()
        btn_2 = tkinter.Button(frm_2, width=8, text=b2)
        btn_2['command'] = self.b2_action
        btn_2.pack(side='left')
        # the enter button will trigger the focused button's action
        btn_1.bind('<KeyPress-Return>', func=self.b1_action)
        btn_2.bind('<KeyPress-Return>', func=self.b2_action)
        # roughly center the box on screen
        # for accuracy see: http://stackoverflow.com/a/10018670/1217270
        root.update_idletasks()
        xp = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)+100
        yp = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        geom = (root.winfo_width(), root.winfo_height(), xp, yp)
        root.geometry('{0}x{1}+{2}+{3}'.format(*geom))
        # call self.close_mod when the close button is pressed
        root.protocol("WM_DELETE_WINDOW", self.close_mod)
        # a trick to activate the window (on windows 7)
        root.deiconify()
        # if t is specified: call time_out after t seconds
        if t: root.after(int(t*1000), func=self.time_out)
        root.bind('<Return>', self.enter_key);
        
    def enter_key(self,event):
        self.b1_action(event);
        #print('enter key pressed!');

    def b1_action(self, event=None):
        try: x = self.entry.get()
        except AttributeError:
            self.returning = self.b1_return
            self.root.quit()
        else:
            #if x:
            self.returning = x
            self.root.quit()

    def b2_action(self, event=None):
        self.returning = self.b2_return
        self.root.quit()


    # remove this function and the call to protocol
    # then the close button will act normally
    def close_mod(self):
        pass

    def time_out(self):
        try: x = self.entry.get()
        except AttributeError: self.returning = None
        else: self.returning = x
        finally: self.root.quit()

    def to_clip(self, event=None):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.msg)
        
        
def mbox(msg, b1='OK', b2='Cancel', text=None, frame=True, t=False, entry=False, width=None):
    """Create an instance of MessageBox, and get data back from the user.
    msg = string to be displayed
    b1 = text for left button, or a tuple (<text for button>, <to return on press>)
    b2 = text for right button, or a tuple (<text for button>, <to return on press>)
    frame = include a standard outerframe: True or False
    t = time in seconds (int or float) until the msgbox automatically closes
    entry = include an entry widget that will have its contents returned: True or False
    """
    msgbox = MessageBox(msg, b1, b2, frame, t, entry, width, text)
    msgbox.root.mainloop()
    # the function pauses here until the mainloop is quit
    msgbox.root.destroy()
    return msgbox.returning

"""
    Saves the newely opened filename to the config file
"""
def saveToConfigFile(configFilename, filename):
    # Save it to file
    configFile = open(configFilename,'w')
    configFile.write(filename)
    configFile.close()

"""
    Loads the last opened filename from the config file
"""
def loadFromConfigFile(confiFilename):
    if os.path.exists(confiFilename):
        configFile = open(confiFilename,'r')
        prevFile = configFile.read()
        configFile.close()
        print('Previously opened file: ',prevFile)
        return prevFile
    return None

"""
    This function handles getting the filename from the user, or if the user
    enters nothing -- the last used filename (from the config file).
"""
def inputFileMBox(configFilename, alternativeSearchPath, extension):
    filename = mbox("Enter video filename:", entry=True, width=100)
    
    if filename=='' or filename is None or filename==False:
        filename = loadFromConfigFile(configFilename)
        if filename is None and alternativeSearchPath is not None and extension is not None:
            filename = findFilenameFromFolder(alternativeSearchPath, extension)
            if filename is None:
                print("Could not find an *.avi file in the folder supplied! exiting...")
                sys.exit()
            
    if filename is not None:
        saveToConfigFile(configFilename, filename)
    return filename

def inputNumberMBox(textQuestionString):
    n = mbox(textQuestionString, entry=True, width=100)
    if n=='' or n is None:
        return None
    return np.float(n)

def boolQuestionMBox(question):
    return mbox(question, "Yes", "No")

def twoOptionQuestionMBox(question, option1, option2):
    return mbox(question, option1, option2)

if __name__=='__main__':
    print(boolQuestionMBox("Unable to load.\rLoad from backup?"))
    