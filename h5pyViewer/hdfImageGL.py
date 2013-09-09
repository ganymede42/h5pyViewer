#!/usr/bin/env python
#*-----------------------------------------------------------------------*
#|                                                                       |
#|  Copyright (c) 2013 by Paul Scherrer Institute (http://www.psi.ch)    |
#|                                                                       |
#|              Author Thierry Zamofing (thierry.zamofing@psi.ch)        |
#*-----------------------------------------------------------------------*
'''
implements an image view to show a colored image of a hdf5 dataset.
'''

if __name__ == '__main__':
    #Used to guarantee to use at least Wx2.8
  import wxversion
  wxversion.ensureMinimal('2.8')
import wx
import os,h5py
import numpy as np
import utilities as ut

try:
  import glumpy
  import wx.glcanvas
  from OpenGL.GL import *
except ImportError as e:
  print 'ImportError: '+e.message

class HdfImageGLFrame(wx.Frame):
  """A simple class for using OpenGL with wxPython."""
  def __init__(self, parent, lbl, hid):
        # Forcing a specific style on the window.
        #   Should this include styles passed?
    style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
    super(HdfImageGLFrame, self).__init__(parent, title=lbl, size=wx.Size(850, 650), style=style)

    self.GLinitialized = False
    attribList = (wx.glcanvas.WX_GL_RGBA,  # RGBA
                  wx.glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
                  wx.glcanvas.WX_GL_DEPTH_SIZE, 24)  # 24 bit

    # Create the canvas
    self.canvas = wx.glcanvas.GLCanvas(self, attribList=attribList)

    # Set the event handlers.
    self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
    self.canvas.Bind(wx.EVT_SIZE, self.processSizeEvent)
    self.canvas.Bind(wx.EVT_PAINT, self.processPaintEvent)
    self.canvas.Bind(wx.EVT_IDLE, self.processIdleEvent)
    t = type(hid)
    if t == h5py.h5d.DatasetID:
      data = h5py.Dataset(hid)
      self.data=data

  def processIdleEvent(self, event):
    try:
      glumpyImg=self.glumpyImg
      data=self.data
      glumpyImgIdx=self.glumpyImgIdx
    except AttributeError as e:
      return
    glumpyImgIdx+=1
    print 'OnIdle',glumpyImgIdx
    frm=data[glumpyImgIdx,...].astype(np.float32)
    glumpyImg.data[:]=frm[:]
    glumpyImg.update()
    self.glumpyImgIdx=glumpyImgIdx
    self.canvas.Refresh(False)

  def processEraseBackgroundEvent(self, event):
    """Process the erase background event."""
    print 'processEraseBackgroundEvent'
    pass # Do nothing, to avoid flashing on MSWin

  def processSizeEvent(self, event):
    """Process the resize event."""
    print 'processSizeEvent'
    if self.canvas.GetContext():
            # Make sure the frame is shown before calling SetCurrent.
      self.Show()
      self.canvas.SetCurrent()

      size = self.canvas.GetClientSize()
      self.OnReshape(size.width, size.height)
      self.canvas.Refresh(False)

    event.Skip()

  def processPaintEvent(self, event):
    """Process the drawing event."""
    print 'processPaintEvent'
    self.canvas.SetCurrent()

    # This is a 'perfect' time to initialize OpenGL ... only if we need to
    if not self.GLinitialized:
      self.OnInitGL()
      self.GLinitialized = True
      size = self.canvas.GetClientSize()
      self.OnReshape(size.width, size.height)
      self.canvas.Refresh(False)

    self.OnDraw()
    event.Skip()

  def OnInitGL(self):
    """Initialize OpenGL for use in the window."""
    print 'OnInitGL'
    glClearColor(1, 1, 1, 1)
    data=self.data
    frm=data[0,...].astype(np.float32)
    self.glumpyImg = glumpy.image.Image(frm, colormap=glumpy.colormap.Hot,vmin=0, vmax=10)
    self.glumpyImg.update()
    self.glumpyImgIdx=0
    pass

  def OnReshape(self, width, height):
    """Reshape the OpenGL viewport based on the dimensions of the window."""
    print 'OnReshape'
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-0.5, 0.5, -0.5, 0.5, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

  def OnDraw(self, *args, **kwargs):
    "Draw the window."
    print 'OnDraw'
    glClear(GL_COLOR_BUFFER_BIT)

    self.glumpyImg.draw(-.49,-.49,0,.98,.98)
    # Drawing an example triangle in the middle of the screen
    #glBegin(GL_TRIANGLES)
    #glColor(1, 0, 0)
    #glVertex(-.25, -.25)
    #glVertex(.25, -.25)
    #glVertex(0, .25)
    #glEnd()
    self.canvas.SwapBuffers()    

if __name__ == '__main__':
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):
    fnHDF='/scratch/detectorData/e14472_00033.hdf5'
    #lbl='mcs'
    lbl='pilatus_1'
    #lbl='spec'
    elem='/entry/dataScan00033/'+lbl
    exampleCmd='--hdfFile='+fnHDF+' --elem='+elem
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__,
                                     epilog='Example:\n'+os.path.basename(sys.argv[0])+' '+exampleCmd+'\n ')
    parser.add_argument('--hdfFile', required=required, default=fnHDF, help='the hdf5 to show')
    parser.add_argument('--elem', required=required, default=elem, help='the path to the element in the hdf5 file')
    return parser
    args = parser.parse_args()
    return args

  class App(wx.App):
    def OnInit(self):
      parser=GetParser()
      #parser=GetParser(False) # debug with exampleCmd
      args = parser.parse_args()
      try:
        self.fid=fid=h5py.h5f.open(args.hdfFile)
      except IOError as e:
        sys.stderr.write('Unable to open File: '+args.hdfFile+'\n')
        parser.print_usage(sys.stderr)
        return True
      try:
        hid = h5py.h5o.open(fid,args.elem)
      except KeyError as e:
        sys.stderr.write('Unable to open Object: '+args.elem+'\n')
        parser.print_usage(sys.stderr)
        return True
      frame = HdfImageGLFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
