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
  from glumpy.graphics import VertexBuffer
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
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    self.GLinitialized = False
    attribList = (wx.glcanvas.WX_GL_RGBA,  # RGBA
                  wx.glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
                  wx.glcanvas.WX_GL_DEPTH_SIZE, 24)  # 24 bit

    # Create the canvas
    self.canvas = wx.glcanvas.GLCanvas(self, attribList=attribList)

    # Set the event handlers.
    self.canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
    self.canvas.Bind(wx.EVT_SIZE, self.OnSize)
    self.canvas.Bind(wx.EVT_PAINT, self.OnPaint)
    self.canvas.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWeel)
    self.canvas.Bind(wx.EVT_MOTION, self.OnMouseEvent)
    self.canvas.Bind(wx.EVT_LEFT_DOWN, self.OnMouseEvent)
    self.canvas.Bind(wx.EVT_LEFT_UP, self.OnMouseEvent)
    #self.canvas.Bind(wx.EVT_IDLE, self.OnIdle)
    t = type(hid)
    if t == h5py.h5d.DatasetID:
      data = h5py.Dataset(hid)
      self.data=data
    self.BuildMenu()

  def BuildMenu(self):
    mnBar = wx.MenuBar()

    #-------- Edit Menu --------
    mn = wx.Menu()
    #mnItem=mn.Append(wx.ID_ANY, 'Setup Colormap', 'Setup the color mapping ');self.Bind(wx.EVT_MENU, self.OnColmapSetup, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Linear Mapping', 'Use a linear values to color mapping ');self.Bind(wx.EVT_MENU, self.OnMapLin, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Log Mapping', 'Use a logarithmic values to color mapping ');self.Bind(wx.EVT_MENU, self.OnMapLog, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Invert X-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    #self.mnIDxAxis=mnItem.GetId()
    #mnItem=mn.Append(wx.ID_ANY, 'Invert Y-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    mnBar.Append(mn, '&Edit')
    mn = wx.Menu()
    #mnItem=mn.Append(wx.ID_ANY, 'Help', 'How to use the image viewer');self.Bind(wx.EVT_MENU, self.OnHelp, mnItem)
    mnBar.Append(mn, '&Help')

    self.SetMenuBar(mnBar)
    self.CreateStatusBar()      


  def OnMouseEvent(self, event):
    if event.ButtonDown(0):
      self.mouseStart=(np.array(event.GetPosition()),self.imgCoord.copy())
      print 'drag Start'
    elif event.ButtonUp(0):
      print 'drag End'
      del self.mouseStart
    else:
      try:
        (pStart,icStart)=self.mouseStart
      except AttributeError as e:
        pSz = np.array(self.canvas.GetClientSize(),np.float32)
        pMouse  = np.array(event.GetPosition(),np.float32)
        ic=self.imgCoord
        pOfs=(ic[0::4]+[.5,.5])*pSz
        tPos=(pMouse-pOfs)/(pSz-2*pOfs)#position on the image 0..1
        print tPos 
        if (tPos<0).any() or (tPos>1).any():
          return
        data=self.data[0,...]
        tPos=tPos*(ic[3::4]-ic[1::4])+ic[1::4]
        tPos[0]*=data.shape[1]
        tPos[1]*=data.shape[0]
        v=tuple(tPos.astype(np.int32))
        v=tuple(reversed(v))
        v+=(data[v],)

        #vS=event.GetPosition()[0]
        self.SetStatusText( "Pos:(%d,%d) Value:%d"%v,0)
        pass
      else: 
        #prefix:
        #p Pixel, t Texture, v vertex
        pSz = np.array(self.canvas.GetClientSize(),np.float32)
        pMouse  = np.array(event.GetPosition(),np.float32)
        ic=self.imgCoord

        pOfs=(ic[0::4]+[.5,.5])*pSz
        tOfs=(pMouse-pStart)/(pSz-2*pOfs)#position on the image 0..1
        tOfs=tOfs*(icStart[3::4]-icStart[1::4])
        
        if icStart[1]-tOfs[0]<0:
          tOfs[0]=icStart[1]
        if icStart[5]-tOfs[1]<0:
          tOfs[1]=icStart[5]
        if icStart[3]-tOfs[0]>1:
          tOfs[0]=icStart[3]-1
        if icStart[7]-tOfs[1]>1:
          tOfs[1]=icStart[7]-1
          
        #print icStart[1::4],icStart[3::4],tOfs

        ic[1::4]=icStart[1::4]-tOfs
        ic[3::4]=icStart[3::4]-tOfs
            
        self.SetZoom()
        self.canvas.Refresh(False)
    #event.Skip()

  def OnMouseWeel(self, event):
    #prefix:
    #p Pixel, t Texture, v vertex
    pSz = np.array(self.canvas.GetClientSize(),np.float32)
    pMouse  = np.array(event.GetPosition(),np.float32)
    ic=self.imgCoord    
    n=event.GetWheelRotation()
    pOfs=(ic[0::4]+[.5,.5])*pSz
    tPos=(pMouse-pOfs)/(pSz-2*pOfs)#position on the image 0..1
    if n>0:
      z=0.3
    else:
      z=-0.3
    tMin=tPos*z
    tMax=tMin+(1.0-z)
    tMin=tMin*(ic[3::4]-ic[1::4])+ic[1::4]
    tMax=tMax*(ic[3::4]-ic[1::4])+ic[1::4]
    tMin[tMin<0]=0
    tMax[tMax>1]=1
    ic[1::4]=tMin
    ic[3::4]=tMax
    #print tPos,pSz,pMouse,n,ic
    self.SetZoom()
    self.canvas.Refresh(False)

    pass

  def OnIdle(self, event):
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

  def OnEraseBackground(self, event):
    """Process the erase background event."""
    print 'OnEraseBackground'
    pass # Do nothing, to avoid flashing on MSWin

  def OnSize(self, event):
    """Process the resize event."""
    print 'OnSize'
    if self.canvas.GetContext():
            # Make sure the frame is shown before calling SetCurrent.
      self.Show()
      self.canvas.SetCurrent()

      size = self.canvas.GetClientSize()
      self.Reshape(size.width, size.height)
      self.canvas.Refresh(False)

    event.Skip()

  def OnPaint(self, event):
    """Process the drawing event."""
    #print 'OnPaint'
    self.canvas.SetCurrent()

    # This is a 'perfect' time to initialize OpenGL ... only if we need to
    if not self.GLinitialized:
      self.InitGL()
      self.GLinitialized = True
      size = self.canvas.GetClientSize()
      self.Reshape(size.width, size.height)
      self.canvas.Refresh(False)

    glClear(GL_COLOR_BUFFER_BIT)
    ic=self.imgCoord
    self.glumpyImg.draw(ic[0],ic[4],0,ic[2]-ic[0],ic[6]-ic[4])
       
    # Drawing an example triangle in the middle of the screen
    #glBegin(GL_TRIANGLES)
    #glColor(1, 0, 0)
    #glVertex(-.25, -.25)
    #glVertex(.25, -.25)
    #glVertex(0, .25)
    #glEnd()
    self.canvas.SwapBuffers()    
    event.Skip()

  def SetZoom(self):
    ic=self.imgCoord
    xmin,xmax,ymin,ymax=ic[1::2];
    vert=self.glumpyImg._vertices
    n = vert.shape[0]
    u,v = np.mgrid[0:n,0:n]
    u=u*(xmax-xmin)/float(n-1)+xmin
    v=v*(ymax-ymin)/float(n-1)+ymin
    #u/=2;u+=.3
    vert['tex_coord']['u'] = u
    vert['tex_coord']['v'] = v

  def InitGL(self):
    """Initialize OpenGL for use in the window."""
    print 'InitGL'
    glClearColor(1, 1, 1, 1)
    data=self.data
    frm=data[0,...].astype(np.float32)
    frm=5.*np.log(data[0,...].astype(np.float32)+1.)
    self.glumpyImg = glumpy.image.Image(frm, colormap=glumpy.colormap.Hot,vmin=0, vmax=10)
    self.glumpyImg.update()
    self.glumpyImgIdx=0
    self.imgCoord=np.array([-.49,0,.49,1,-.49,0,.49,1])#xmin,xmax,umin,umax,ymin,ymax,vmin,vmax    
    pass

  def Reshape(self, width, height):
    """Reshape the OpenGL viewport based on the dimensions of the window."""
    print 'Reshape'
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-0.5, 0.5, -0.5, 0.5, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

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
