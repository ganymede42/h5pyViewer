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
import matplotlib as mpl
if __name__ == '__main__':
  mpl.use('WXAgg')
  #or mpl.use('WX')
  #matplotlib.get_backend()

import os,h5py
import numpy as np
import utilities as ut
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import pylab as plt #used for the colormaps
#or from matplotlib.backends.backend_wx import FigureCanvasWx as FigureCanvas
#The source of the DraggableColorbar is from:
#http://www.ster.kuleuven.be/~pieterd/python/html/plotting/interactive_colorbar.html

class MPLCanvasImg(FigureCanvas):
  def __init__(self,parent,SetStatusCB=None):
    if SetStatusCB:
      self.SetStatusCB=SetStatusCB
    fig = mpl.figure.Figure()
    ax = fig.add_axes([0.075,0.1,0.75,0.85])
    FigureCanvas.__init__(self,parent, -1, fig)
    self.mpl_connect('motion_notify_event', self.OnMotion)
    self.mpl_connect('button_press_event',   self.OnBtnPress) 
    self.mpl_connect('button_release_event', self.OnBtnRelease) 
    self.mpl_connect('scroll_event', self.OnBtnScroll)
    self.mpl_connect('key_press_event',self.OnKeyPress) 
    self.fig=fig
    self.ax=ax
  
  def InitChild(self,data):
    fig=self.fig
    ax=self.ax
    avg=np.average(data); std=np.std(data)
    vmin=np.min(data);vmax=np.max(data)
    vmin=max(vmin,avg-3*std);vmax=min(vmax,avg+3*std)
    img = ax.imshow(data,interpolation='nearest',cmap=mpl.cm.jet, vmin=vmin, vmax=vmax)
    colBar=fig.colorbar(img,orientation='vertical')
    self.colBar=colBar
    self.colCycle = sorted([i for i in dir(plt.cm) if hasattr(getattr(plt.cm,i),'N')])
    self.colIndex = self.colCycle.index(colBar.get_cmap().name)
    self.img=img
 
  def OnMotion(self,event):
    #print event,event.x,event.y,event.inaxes,event.xdata,event.ydata
    if event.inaxes==self.ax:
      x=int(round(event.xdata))
      y=int(round(event.ydata))
      try:
        v=self.img.get_array()[y,x]
      except IndexError as e:
        pass
      else:
        #print x,y,v
        self.SetStatusCB(self.Parent,0,(x,y,v))
    elif event.inaxes==self.colBar.ax:
      colBar=self.colBar
      pt=colBar.ax.bbox.get_points()[:,1]
      nrm=colBar.norm
      vmin,vmax,p0,p1,pS = (nrm.vmin,nrm.vmax,pt[0],pt[1],event.y)
      if isinstance(colBar.norm,mpl.colors.LogNorm):#type(colBar.norm)==mpl.colors.LogNorm does not work...
        vS=0
      else:#scale around point
        vS=vmin+(vmax-vmin)/(p1-p0)*(pS-p0)
      self.SetStatusCB(self.Parent,1,vS)
    try:
      vmin,vmax,p0,p1,pS=self.colBarPressed
    except AttributeError:
      return
      #if event.inaxes != self.cbar.ax: return
    colBar=self.colBar
    #print vmin,vmax,p0,p1,pS,type(colBar.norm)
    #print 'x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f'%(x0, xpress, event.xdata, dx, x0+dx)
    
    if isinstance(colBar.norm,mpl.colors.LogNorm):#type(colBar.norm)==mpl.colors.LogNorm does not work...
      if event.button==1:
        #colBar.norm.vmin=.1
        colBar.norm.vmax=vmax*np.exp((pS-event.y)/100)
        #scale= np.exp((event.y-pS)/100)       
    elif event.button==1:#move top,bottom,both
      pD = event.y - pS
      vD=(vmax-vmin)/(p1-p0)*(pS-event.y)
      colBar.norm.vmin = vmin+vD
      colBar.norm.vmax = vmax+vD
    elif event.button==3:#scale around point
      scale= np.exp((pS-event.y)/100)
      vS=vmin+(vmax-vmin)/(p1-p0)*(pS-p0)
      #print scale,vS
      colBar.norm.vmin = vS-scale*(vS-vmin)
      colBar.norm.vmax = vS-scale*(vS-vmax)
    self.img.set_norm(colBar.norm)#force image to redraw
    colBar.patch.figure.canvas.draw()      
      
  def OnBtnPress(self, event):
    """on button press we will see if the mouse is over us and store some data"""
    #print dir(event.guiEvent)
    if event.inaxes == self.colBar.ax:
      #if event.guiEvent.LeftDClick()==True:
      #    print dlg
      pt=self.colBar.ax.bbox.get_points()[:,1]
      nrm=self.colBar.norm
      self.colBarPressed = (nrm.vmin,nrm.vmax,pt[0],pt[1],event.y)
      #self.colBarPressed = event.x, event.y
      #print self.colBarPressed
      #self.OnMouse(event)
    pass

  def OnBtnRelease(self, event):
    """on release we reset the press data"""
    #self.OnMouse(event)
    try: del self.colBarPressed
    except AttributeError: pass
  
  def OnBtnScroll(self, event):
    #self.OnMouse(event)
    colBar=self.colBar
    if event.inaxes==colBar.ax:
      pt=colBar.ax.bbox.get_points()[:,1]
      nrm=colBar.norm
      vmin,vmax,p0,p1,pS = (nrm.vmin,nrm.vmax,pt[0],pt[1],event.y)
      if isinstance(colBar.norm,mpl.colors.LogNorm):#type(colBar.norm)==mpl.colors.LogNorm does not work...
        scale= np.exp((-event.step)/10)
        colBar.norm.vmax=vmax*scale
      else:#scale around point
        scale= np.exp((-event.step)/10)
        vS=vmin+(vmax-vmin)/(p1-p0)*(pS-p0)
        #print scale,vS
        colBar.norm.vmin = vS-scale*(vS-vmin)
        colBar.norm.vmax = vS-scale*(vS-vmax)
      self.img.set_norm(colBar.norm)#force image to redraw
      colBar.patch.figure.canvas.draw()        

  def OnKeyPress(self, event):
    colCycle=self.colCycle
    colBar=self.colBar
    if event.key=='down':
      self.colIndex += 1
    elif event.key=='up':
      self.colIndex -= 1
    self.colIndex%=len(colCycle)
    cmap = colCycle[self.colIndex]
    colBar.set_cmap(cmap)
    colBar.draw_all()
    self.img.set_cmap(cmap)
    self.img.get_axes().set_title(cmap)
    colBar.patch.figure.canvas.draw()

  def OnMouse(self, event):
    for k in dir(event):
      if k[0]!='_':
        print k,getattr(event,k)

class DlgColBarSetup(wx.Dialog):
  def __init__(self,parent):
    wx.Dialog.__init__(self,parent,-1,'Colormap Setup')
    colBar=parent.canvas.colBar
    cmap=colBar.cmap
    nrm=colBar.norm
    txtVMin=wx.StaticText(self,-1,'vmin')
    txtVMax=wx.StaticText(self,-1,'vmax')
    self.edVMin=edVMin=wx.TextCtrl(self,-1,'%g'%nrm.vmin)
    self.edVMax=edVMax=wx.TextCtrl(self,-1,'%g'%nrm.vmax)
    sizer=wx.BoxSizer(wx.VERTICAL)
    fgs=wx.FlexGridSizer(3,2,5,5)
    fgs.Add(txtVMin,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMin,0,wx.EXPAND)
    fgs.Add(txtVMax,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMax,0,wx.EXPAND)
    sizer.Add(fgs,0,wx.EXPAND|wx.ALL,5)

    edVMin.SetFocus()

    btns =  self.CreateButtonSizer(wx.OK|wx.CANCEL)
    sizer.Add(btns,0,wx.EXPAND|wx.ALL,5)
    self.Bind(wx.EVT_BUTTON, self.OnBtnOk, id=wx.ID_OK)

    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnBtnOk(self, event):
    event.Skip()#do not consume (use event to close the window and sent return code)
    print 'OnBtnOk'
    parent=self.GetParent()
    canvas=parent.canvas
    colBar=canvas.colBar
    colBar.norm.vmin=float(self.edVMin.Value)
    colBar.norm.vmax=float(self.edVMax.Value)
    canvas.img.set_norm(colBar.norm)
    #colBar.patch.figure.canvas.draw()
    canvas.draw()      
  
class HdfImageFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(850, 650))
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      data=h5py.Dataset(hid)

    canvas =  MPLCanvasImg(self,self.SetStatusCB)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
    self.SetSizer(sizer)

    toolbar=ut.AddToolbar(canvas,sizer)  

    wxAxCtrlLst=[]
    l=len(data.shape)
    idxXY=(l-2,l-1)
    for idx,l in enumerate(data.shape):
      if idx in idxXY:
        continue 
      wxAxCtrl=ut.SliderGroup(self, label='Axis:%d'%idx,range=(0,l-1))
      wxAxCtrl.idx=idx
      wxAxCtrlLst.append(wxAxCtrl)
      sizer.Add(wxAxCtrl.sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)
      wxAxCtrl.SetCallback(HdfImageFrame.OnSetView,wxAxCtrl)

    sl=ut.GetSlice(idxXY,data.shape,wxAxCtrlLst)
    
    canvas.InitChild(data[sl])
      
    #self.Fit()   
    self.Centre()
    
    self.BuildMenu()
    self.canvas=canvas
    self.sizer=sizer
    self.toolbar=toolbar
    self.data=data
    self.idxXY=idxXY
    self.wxAxCtrlLst=wxAxCtrlLst
 
  def BuildMenu(self):
    mnBar = wx.MenuBar()

    #-------- Edit Menu --------
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Setup Colormap', 'Setup the color mapping ');self.Bind(wx.EVT_MENU, self.OnColmapSetup, mnItem)
    mnItem=mn.Append(wx.ID_ANY, 'Linear Mapping', 'Use a linear values to color mapping ');self.Bind(wx.EVT_MENU, self.OnMapLin, mnItem)
    mnItem=mn.Append(wx.ID_ANY, 'Log Mapping', 'Use a logarithmic values to color mapping ');self.Bind(wx.EVT_MENU, self.OnMapLog, mnItem)
    mnItem=mn.Append(wx.ID_ANY, 'Invert X-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    self.mnIDxAxis=mnItem.GetId()
    mnItem=mn.Append(wx.ID_ANY, 'Invert Y-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    mnBar.Append(mn, '&Edit')
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Help', 'How to use the image viewer');self.Bind(wx.EVT_MENU, self.OnHelp, mnItem)
    mnBar.Append(mn, '&Help')

    self.SetMenuBar(mnBar)
    self.CreateStatusBar()      
        
  def SetIdxXY(self,x,y):
    self.idxXY=(x,y)
 
  @staticmethod
  def SetStatusCB(obj,mode,v):
    if mode==0:
      obj.SetStatusText( "x= %d y=%d val=%g"%v,0)
    elif mode==1:
      obj.SetStatusText( "Colormap Value %d (drag to scale)"%v,0)
    else:
      raise KeyError('wrong mode')

  @staticmethod
  def OnSetView(usrData,value,msg):
    'called when a slice is selected with the slider controls'
    imgFrm=usrData.slider.Parent
    #imgFrm.img.set_array(imgFrm.data[usrData.value,...])
    data=imgFrm.data
    sl=ut.GetSlice(imgFrm.idxXY,data.shape,imgFrm.wxAxCtrlLst)
    imgFrm.canvas.img.set_array(data[sl])
    imgFrm.canvas.draw()
    pass

  def OnHelp(self,event):
    msg='''to change the image selection:
use the toolbar at the bottom to pan and zoom the image
use the scrollbars at the bottom (if present) to select an other slice

to change the colorscale:
drag with left mouse button to move the colorbar up and down
drag with right mouse button to zoom in/out the colorbar at a given point
use mouse weel to zoom in/out the colorbar at a given point
double click left mouse button to set maximum and minimun colorbar values
use cursor up and down to use a different colormap'''
    dlg = wx.MessageDialog(self, msg, 'Help', wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()
  
  def OnColmapSetup(self,event):
    dlg=DlgColBarSetup(self)
    if dlg.ShowModal()==wx.ID_OK:
      pass
    dlg.Destroy()

  def OnMapLin(self,event):
    img=self.canvas.img
    data=img.get_array()
    colBar=self.canvas.colBar
    avg=np.average(data); std=np.std(data)
    vmin=np.min(data);vmax=np.max(data)
    vmin=max(vmin,avg-3*std);vmax=min(vmax,avg+3*std)
    #print vmin, vmax
    colBar.norm = mpl.colors.Normalize(vmin, vmax)
    img.set_norm(colBar.norm)
    colBar.patch.figure.canvas.draw()      

  def OnMapLog(self,event):
    #print self.colBar.norm,self.img.norm
    img=self.canvas.img
    ax=self.canvas.ax
    colBar=self.canvas.colBar
    data=img.get_array()
    img.cmap._init();bg=img.cmap._lut[0].copy();bg[:-1]/=4
    ax.set_axis_bgcolor(bg)
    avg=np.average(data); std=np.std(data)
    vmin=1;vmax=avg+3*std
    colBar.norm = mpl.colors.LogNorm(vmin,vmax)
    #print vmin, vmax
    img.set_norm(colBar.norm)
    colBar.patch.figure.canvas.draw()      

  def OnInvertAxis(self,event):
    ax=self.canvas.ax
    #event.Checked()
    if self.mnIDxAxis==event.GetId():
      ax.invert_xaxis()
    else:
      ax.invert_yaxis()
    self.canvas.draw() 
    pass
       
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
      frame = HdfImageFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
