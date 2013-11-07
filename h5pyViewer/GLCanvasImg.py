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

import wx
#import os,h5py
import numpy as np

import glumpy
from glumpy.graphics import VertexBuffer
import wx.glcanvas
from OpenGL.GL import *
#from scipy import ndimage as ndi

def MplAddColormap(m,lut):
  if type(lut)==dict:
    try:
      lstR=lut['red']
      lstG=lut['green']
      lstB=lut['blue']
      kR,vR,dummy=zip(*lstR)
      kG,vG,dummy=zip(*lstG)
      kB,vB,dummy=zip(*lstB)
    except TypeError as e:
      print 'failed to add '+m+' (probably some lambda function)'
      #print lut
      return
    kLst=set()
    kLst.update(kR)
    kLst.update(kG)
    kLst.update(kB)
    kLst=sorted(kLst)
    vRGB=zip(np.interp(kLst, kR, vR),np.interp(kLst, kG, vG),np.interp(kLst, kB, vB))
    lut2=zip(kLst,vRGB)
  else:
    if type(lut[0][1])==tuple:
      lut2=lut
    else:
      kLst=np.linspace(0., 1., num=len(lut))
      lut2=zip(kLst,lut)
  
  #cmap = Colormap('gray',(0., (0.,0.,0.,1.)),(1., (1.,1.,1.,1.)))
  cm2=glumpy.colormap.Colormap(m,*tuple(lut2))
  setattr(glumpy.colormap,m,cm2)  
  
def MplAddAllColormaps(colMapNameLst=None):
  try:
    import matplotlib.cm as cm
  except ImportError as e:
    print 'ImportError: '+e.message
  if not colMapNameLst:
    colMapNameLst=[m for m in cm.datad if not m.endswith("_r")]
  for m in colMapNameLst:
    lut= cm.datad[m]
    MplAddColormap(m,lut)
  pass 

class GLCanvasImg(wx.glcanvas.GLCanvas):
  """A simple class for using OpenGL with wxPython."""
  def __init__(self,parent,SetStatusCB=None):
    if SetStatusCB:
      self.SetStatusCB=SetStatusCB
    self.GLinitialized = False
    attribList = (wx.glcanvas.WX_GL_RGBA,  # RGBA
                  wx.glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
                  wx.glcanvas.WX_GL_DEPTH_SIZE, 24)  # 24 bit

    # Create the canvas
    #self.canvas = wx.glcanvas.GLCanvas(parent, attribList=attribList)
    wx.glcanvas.GLCanvas.__init__(self, parent, attribList=attribList)

    # Set the event handlers.
    self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
    self.Bind(wx.EVT_SIZE, self.OnSize)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWeel)
    self.Bind(wx.EVT_MOTION, self.OnMouseEvent)
    self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseEvent)
    self.Bind(wx.EVT_LEFT_UP, self.OnMouseEvent)
    
  def OnMouseEvent(self, event):
    try:
      data=self.data
    except AttributeError:
      return
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
        pSz = np.array(self.GetClientSize(),np.float32)
        pMouse  = np.array(event.GetPosition(),np.float32)
        ic=self.imgCoord
        pOfs=(ic[0::4]+[.5,.5])*pSz
        tPos=(pMouse-pOfs)/(pSz-2*pOfs)#position on the image 0..1
        #print tPos 
        if (tPos<0).any() or (tPos>1).any(): return
        tPos=tPos*(ic[3::4]-ic[1::4])+ic[1::4]
        tPos[0]*=data.shape[1]
        tPos[1]*=data.shape[0]
        v=tuple(tPos.astype(np.int32))
        #v=tuple(reversed(v))
        v+=(data[tuple(reversed(v))],)
        self.SetStatusCB(self.Parent,0,v)

        #vS=event.GetPosition()[0]
        pass
      else: 
        #prefix:
        #p Pixel, t Texture, v vertex
        pSz = np.array(self.GetClientSize(),np.float32)
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
        self.Refresh(False)
    #event.Skip()
    pass

  def OnMouseWeel(self, event):
    #prefix:
    #p Pixel, t Texture, v vertex
    pSz = np.array(self.GetClientSize(),np.float32)
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
    self.Refresh(False)

    pass

  def OnEraseBackground(self, event):
    """Process the erase background event."""
    #print 'OnEraseBackground'
    pass # Do nothing, to avoid flashing on MSWin

  def OnSize(self, event):
    """Process the resize event."""
    #print 'OnSize'
    if self.GetContext():
            # Make sure the frame is shown before calling SetCurrent.
      self.Show()
      self.SetCurrent()

      size = self.GetClientSize()
      self.Reshape(size.width, size.height)
      self.Refresh(False)

    event.Skip()

  def OnPaint(self, event):
    """Process the drawing event."""
    #print 'OnPaint'
    self.SetCurrent()

    # This is a 'perfect' time to initialize OpenGL ... only if we need to
    if not self.GLinitialized:
      self.InitGL()
      self.GLinitialized = True
      size = self.GetClientSize()
      self.Reshape(size.width, size.height)
      self.Refresh(False)

    glClear(GL_COLOR_BUFFER_BIT)
    ic=self.imgCoord
    try: glImg=self.glImg
    except AttributeError: pass
    else:  self.glImg.draw(ic[0],ic[4],0,ic[2]-ic[0],ic[6]-ic[4])
    self.glColBar.draw(-.5,-.5,0,1.,.02)       
    # Drawing an example triangle in the middle of the screen
    #glBegin(GL_TRIANGLES)
    #glColor(1, 0, 0)
    #glVertex(-.25, -.25)
    #glVertex(.25, -.25)
    #glVertex(0, .25)
    #glEnd()
    self.SwapBuffers()
    if event!=None:
      event.Skip()

  def OnHelp(self,event):
    msg='''to change the image selection:
drag with left mouse button to move the image
use mouse wheel to zoom in/out the image at a given point
'''
    dlg = wx.MessageDialog(self, msg, 'Help', wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

  def OnColmapSetup(self,event):
    dlg=DlgColBarSetup(self)
    if dlg.ShowModal()==wx.ID_OK:
      pass
    dlg.Destroy()
    
  def SetZoom(self):
    ic=self.imgCoord
    xmin,xmax,ymin,ymax=ic[1::2];
    vert=self.glImg._vertices
    n = vert.shape[0]
    u,v = np.mgrid[0:n,0:n]
    u=u*(xmax-xmin)/float(n-1)+xmin
    v=v*(ymax-ymin)/float(n-1)+ymin
    #u/=2;u+=.3
    vert['tex_coord']['u'] = u
    vert['tex_coord']['v'] = v


  def UpdateImg(self):
    try:
      txrData=self.GetTxrData()
    except AttributeError as e:
      return
    try:
      glImg=self.glImg
    except AttributeError as e:
      colMap=self.glColBar._filter.colormap
      txrRng=self.GetTxrRange()
      self.glImg=glImg=glumpy.image.Image(txrData, colormap=colMap,vmin=txrRng[0], vmax=txrRng[1])
    else:
      if glImg.data.shape==self.data.shape:
        glImg.data[:]=txrData[:]
      else:
        self.glImg=glImg=glumpy.image.Image(txrData, colormap=colMap,vmin=glImg._vmin, vmax=glImg._vmax)   
    glImg.update()

  def GetTxrRange(self):
    txrTrfFunc=self.txrTrfFunc
    dataRange=self.dataRange
    if txrTrfFunc==0:
      return dataRange
    elif txrTrfFunc==1:
      return (0,np.log(1+dataRange[1]-dataRange[0]))
  
  def AutoRange(self,txrTrfFunc):
    data=self.data
    self.txrTrfFunc=txrTrfFunc
    if txrTrfFunc==0:
      avg=np.average(data); std=np.std(data)
      vmin=data.min();vmax=data.max()
      vmin=max(vmin,avg-3*std);vmax=min(vmax,avg+3*std)      
    elif txrTrfFunc==1:
      avg=np.average(data); std=np.std(data)     
      vmin=data.min();vmax=data.max()
      vmin=max(vmin,avg-3*std);vmax=min(vmax,avg+3*std)                 
    self.dataRange=(vmin,vmax)

  def GetTxrData(self):
    data=self.data
    try:
      txrTrfFunc=self.txrTrfFunc
    except AttributeError as e:
      self.AutoRange(1)     
      txrTrfFunc=self.txrTrfFunc

    if txrTrfFunc==0:
      if data.dtype==np.float32:
        txrData=data
      else:
        txrData=data[...].astype(np.float32)
    elif txrTrfFunc==1:
      ofs=1.-self.dataRange[0]
      txrData=np.log(data[...].astype(np.float32)+ofs)
    return txrData
  
  def InitGL(self):
    """Initialize OpenGL for use in the window."""
    #print 'InitGL'
    glClearColor(.2, .2, .2, 1)
    colMap=glumpy.colormap.Hot
    txrColBar=np.linspace(0.,1., 256).astype(np.float32)
    self.glColBar=glumpy.image.Image(txrColBar, colormap=colMap,vmin=0, vmax=1)
   
    self.UpdateImg()
    self.imgCoord=np.array([-.49,0,.49,1,-.49,0,.49,1])#xmin,xmax,umin,umax,ymin,ymax,vmin,vmax    
    pass

  def Reshape(self, width, height):
    """Reshape the OpenGL viewport based on the dimensions of the window."""
    #print 'Reshape'
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-0.5, 0.5, -0.5, 0.5, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

class DlgColBarSetup(wx.Dialog):
  def __init__(self,parent):
    wx.Dialog.__init__(self,parent,-1,'Colormap Setup')
    #glImg=parent.glImg
    #glColBar=parent.glColBar
    dataRange=parent.dataRange   
    txtVMin=wx.StaticText(self,-1,'vmin')
    txtVMax=wx.StaticText(self,-1,'vmax')
    txtColMap=wx.StaticText(self,-1,'colormap')   
    self.edVMin=edVMin=wx.TextCtrl(self,-1,'%g'%dataRange[0],style=wx.TE_PROCESS_ENTER)
    self.edVMax=edVMax=wx.TextCtrl(self,-1,'%g'%dataRange[1],style=wx.TE_PROCESS_ENTER)

    txtTxrFunc=wx.StaticText(self,-1,'function')   
    self.cbtxrFunc=cbtxrFunc=wx.ComboBox(self, -1, choices=('linear','logarithmic'), style=wx.CB_READONLY)
    cbtxrFunc.SetSelection(parent.txrTrfFunc)
    
    colMapLst=[]
    #adding all existing colormaps
    #MplAddAllColormaps()
    #for (k,v) in glumpy.colormap.__dict__.iteritems():
    #  if isinstance(v,glumpy.colormap.Colormap):
    #    colMapLst.append(k)
        
    #adding best existing colormaps of glumpy and mpl
    for k in ('Hot','spectral','jet','Grey','RdYlBu','hsv','gist_stern','gist_rainbow','IceAndFire','gist_ncar'):
      try:
        v=glumpy.colormap.__dict__[k]
      except KeyError as e:
        try:
          import matplotlib.cm as cm
          lut= cm.datad[k]
          MplAddColormap(k,lut)
          v=glumpy.colormap.__dict__[k]
        except ImportError as e:
          print e.message
          print "don't have colormap "+k
          continue
      if isinstance(v,glumpy.colormap.Colormap):
        colMapLst.append(k)

    self.cbColMap=cbColMap=wx.ComboBox(self, -1, choices=colMapLst, style=wx.CB_READONLY)
    cbColMap.Value=parent.glImg._filter.colormap.name
    
    sizer=wx.BoxSizer(wx.VERTICAL)
    fgs=wx.FlexGridSizer(4,2,5,5)
    fgs.Add(txtVMin,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMin,0,wx.EXPAND)
    fgs.Add(txtVMax,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMax,0,wx.EXPAND)
    fgs.Add(txtTxrFunc,0,wx.ALIGN_RIGHT)
    fgs.Add(cbtxrFunc,0,wx.EXPAND)
    fgs.Add(txtColMap,0,wx.ALIGN_RIGHT)
    fgs.Add(cbColMap,0,wx.EXPAND)
    sizer.Add(fgs,0,wx.EXPAND|wx.ALL,5)

    edVMin.SetFocus()

    btns =  self.CreateButtonSizer(wx.OK|wx.CANCEL)
    btnApply=wx.Button(self, -1, 'Apply')
    btns.Add(btnApply, 0, wx.ALL, 5)
    sizer.Add(btns,0,wx.EXPAND|wx.ALL,5)
    self.Bind(wx.EVT_BUTTON, self.OnModify, id=wx.ID_OK)
    self.Bind(wx.EVT_BUTTON, self.OnModify, btnApply)
    #self.Bind(wx.EVT_TEXT_ENTER, self.OnModify, edVMin)
    #self.Bind(wx.EVT_TEXT_ENTER, self.OnModify, edVMax)
    self.Bind(wx.EVT_TEXT, self.OnModify, edVMin)
    self.Bind(wx.EVT_TEXT, self.OnModify, edVMax)
    self.Bind(wx.EVT_COMBOBOX, self.OnModify, cbtxrFunc)
    self.Bind(wx.EVT_COMBOBOX, self.OnModify, cbColMap)

    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnModify(self, event):
    #print 'OnModify'
    parent=self.GetParent()
    glImg=parent.glImg
    glColBar=parent.glColBar

    v=self.cbColMap.Value
    if v!=glImg._filter.colormap.name:
      cmap=getattr(glumpy.colormap,v)
      glImg._filter.colormap=cmap
      glImg._filter.build()
      glColBar._filter.colormap=cmap
      glColBar._filter.build()
      glColBar.update()   
    
    parent.dataRange=(float(self.edVMin.Value),float(self.edVMax.Value))
    v=self.cbtxrFunc.GetCurrentSelection()
    if v==1 or v!=parent.txrTrfFunc:
      parent.txrTrfFunc=v  
      txrRange=parent.GetTxrRange()   
      glImg._vmin, glImg._vmax = txrRange
      parent.UpdateImg()
    else:
      txrRange=parent.GetTxrRange()   
      glImg._vmin, glImg._vmax = txrRange
      glImg.update()
    parent.Refresh(False)
    if event.GetId()==wx.ID_OK:
      event.Skip()#do not consume (use event to close the window and sent return code)
  