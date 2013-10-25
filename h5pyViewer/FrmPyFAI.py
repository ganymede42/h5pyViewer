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
import os,h5py
from GLCanvasImg import *
import pyFAI
from hdfImageGL import HdfImageGLFrame
from glumpy.image.texture import Texture
from scipy import ndimage as ndi

def FindCenter(arr):
  m=ndi.median_filter(arr, 5)
  sx=m.sum(1)
  sy=m.sum(0)
  shape=arr.shape
  xx=np.arange(shape[0])
  yy=np.arange(shape[1])    
  x=(xx*sx).sum()/sx.sum()
  y=(yy*sy).sum()/sy.sum()
  #print x,y
  #import pylab as plt #used for the colormaps
  #plt.figure()
  #plt.subplot(211)
  #plt.plot(sx)
  #plt.subplot(212)
  #plt.plot(sy)
  #plt.show(block=False)
  return (x,y)

class MPLCanvasPyFAI1D(FigureCanvas):
  def __init__(self,parent,SetStatusCB=None):
    if SetStatusCB:
      self.SetStatusCB=SetStatusCB
    fig = mpl.figure.Figure()
    ax = fig.add_axes([0.075,0.1,0.75,0.85])
    FigureCanvas.__init__(self,parent, -1, fig)
    #self.mpl_connect('motion_notify_event', self.OnMotion)
    #self.mpl_connect('button_press_event',   self.OnBtnPress) 
    #self.mpl_connect('button_release_event', self.OnBtnRelease) 
    #self.mpl_connect('scroll_event', self.OnBtnScroll)
    #self.mpl_connect('key_press_event',self.OnKeyPress) 
    self.fig=fig
    self.ax=ax
  
  def InitChild(self,data):
    fig=self.fig
    ax=self.ax
    ctrX,ctrY=self.center=FindCenter(data)
    self.ai = pyFAI.AzimuthalIntegrator(1.e3, ctrX, ctrY, 0.0, 0.0, 0.0, 1.e0, 1.e0) 
    #canvas=self.canvas
    self.numPtTh=int(np.average(data.shape)/2.)
    out=self.ai.xrpd(data,self.numPtTh)
    self.hl=ax.plot(*out)
    ax.set_yscale('log')
    #canvas.data=imgPolar
    #print imgPolar.shape
    #out=ai.xrpd(imgData,1000)
    #out=ai.xrpd_OpenCL(imgData,1000)
    #import pylab
    #pylab.plot(*out)
    #pylab.yscale("log")
    #pylab.show()


  
class HdfPyFAI1DFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(850, 650))
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      data=h5py.Dataset(hid)

    canvas =  MPLCanvasPyFAI1D(self,self.SetStatusCB)

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
      wxAxCtrl.SetCallback(HdfPyFAI1DFrame.OnSetView,wxAxCtrl)

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

    hl=imgFrm.canvas.hl
    ai=imgFrm.canvas.ai
    numPtTh=imgFrm.canvas.numPtTh
    out=ai.xrpd(data[sl],numPtTh)
    hl[0].set_ydata(out[1])
    imgFrm.canvas.draw()
    pass


###########################################

class HdfPyFAIFrame(HdfImageGLFrame):
  def __init__(self, parent, title, hid):
    HdfImageGLFrame.__init__(self, parent, title, hid)
    #HdfPyFAI1DFrame(self, title, hid)
    canvas=self.canvas
    raw=canvas.data
    ctrX,ctrY=FindCenter(raw)
    self.ai = pyFAI.AzimuthalIntegrator(1.e3, ctrX, ctrY, 0.0, 0.0, 0.0, 1.e0, 1.e0) 
    
    raw
    self.numPtTh=int(np.average(raw.shape)/2.)
    self.numPtCh=360
    
    imgPolar,theta,chi=self.ai.xrpd2(raw,self.numPtTh,self.numPtCh)
    canvas.data=imgPolar
    print imgPolar.shape

  def BuildMenu(self):
    HdfImageGLFrame.BuildMenu(self)
    mnBar=self.GetMenuBar()
    mn=mnBar.GetMenu(0)
    itemLst=mn.GetMenuItems()
    it=itemLst[0]
    it.GetItemLabel()
    mnItem=mn.Append(wx.ID_ANY, 'Setup FAI', 'Setup fast azimutal integration ');self.Bind(wx.EVT_MENU, self.OnFAISetup, mnItem)

  @staticmethod
  def OnSetView(usrData,value,msg):
    'called when a slice is selected with the slider controls'
    frm=usrData.slider.Parent
    ds=frm.dataSet
    canvas=frm.canvas
    glImg=canvas.glImg
    sl=ut.GetSlice(frm.idxXY,ds.shape,frm.wxAxCtrlLst)
    imgPolar,theta,chi=frm.ai.xrpd2(ds[sl],frm.numPtTh,frm.numPtCh)
    canvas.data[:]=imgPolar[:]
    glImg.data[:]=canvas.GetTxrData()
    glImg.update()
    canvas.OnPaint(None)#force to repaint, Refresh and Update do not force !
    #canvas.Refresh(False)
    #canvas.Update()
    pass

  def OnFAISetup(self, event):
    dlg=DlgSetupPyFAI(self)
    if dlg.ShowModal()==wx.ID_OK:
      pass
    dlg.Destroy()


class DlgSetupPyFAI(wx.Dialog):
  def __init__(self,parent):
    wx.Dialog.__init__(self,parent,-1,'pyFAI Setup')
    ai=parent.ai
    #glColBar=parent.glColBar
    #dataRange=parent.dataRange   
    txtCtrX=wx.StaticText(self,-1,'center X')
    txtCtrY=wx.StaticText(self,-1,'center Y')
    txtNumPtTh=wx.StaticText(self,-1,'number of pt in Theta')
    txtNumPtCh=wx.StaticText(self,-1,'number of pt in Chi')  
    txtMethod=wx.StaticText(self,-1,'method')   



    self.edCtrX=edCtrX=wx.TextCtrl(self,-1,'%g'%ai.get_poni1(),style=wx.TE_PROCESS_ENTER)
    self.edCtrY=edCtrY=wx.TextCtrl(self,-1,'%g'%ai.get_poni2(),style=wx.TE_PROCESS_ENTER)
    self.edNumPtTh=edNumPtTh=wx.TextCtrl(self,-1,'%g'%parent.numPtTh,style=wx.TE_PROCESS_ENTER)
    self.edNumPtCh=edNumPtCh=wx.TextCtrl(self,-1,'%g'%parent.numPtCh,style=wx.TE_PROCESS_ENTER)
    self.cbMethod=cbMethod=wx.ComboBox(self, -1, choices=('default','numny'), style=wx.CB_READONLY)
    #cbtxrFunc.SetSelection(parent.txrTrfFunc)
    
    sizer=wx.BoxSizer(wx.VERTICAL)
    fgs=wx.FlexGridSizer(4,2,5,5)
    fgs.Add(txtCtrX,0,wx.ALIGN_RIGHT)
    fgs.Add(edCtrX,0,wx.EXPAND)
    fgs.Add(txtCtrY,0,wx.ALIGN_RIGHT)
    fgs.Add(edCtrY,0,wx.EXPAND)
    fgs.Add(txtNumPtTh,0,wx.ALIGN_RIGHT)
    fgs.Add(edNumPtTh,0,wx.EXPAND)
    fgs.Add(txtNumPtCh,0,wx.ALIGN_RIGHT)
    fgs.Add(edNumPtCh,0,wx.EXPAND)
    fgs.Add(txtMethod,0,wx.ALIGN_RIGHT)
    fgs.Add(cbMethod,0,wx.EXPAND)
    sizer.Add(fgs,0,wx.EXPAND|wx.ALL,5)

    #edVMin.SetFocus()

    btns =  self.CreateButtonSizer(wx.OK|wx.CANCEL)
    btnApply=wx.Button(self, -1, 'Apply')
    btns.Add(btnApply, 0, wx.ALL, 5)
    sizer.Add(btns,0,wx.EXPAND|wx.ALL,5)
    self.Bind(wx.EVT_BUTTON, self.OnModify, id=wx.ID_OK)
    self.Bind(wx.EVT_BUTTON, self.OnModify, btnApply)
    #self.Bind(wx.EVT_TEXT, self.OnModify, edCtrX)
    #self.Bind(wx.EVT_TEXT, self.OnModify, edCtrY)
    #self.Bind(wx.EVT_TEXT, self.OnModify, edNumSector)
    self.Bind(wx.EVT_COMBOBOX, self.OnModify, cbMethod)
    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnModify(self, event):
    print 'OnModify'
    frm=self.GetParent() 
    ds=frm.dataSet
    canvas=frm.canvas
    glImg=canvas.glImg
    ai=frm.ai
    ai.set_poni1(float(self.edCtrX.Value))
    ai.set_poni2(float(self.edCtrY.Value))
    frm.numPtTh=int(self.edNumPtTh.Value)
    frm.numPtCh=int(self.edNumPtCh.Value)
    sl=ut.GetSlice(frm.idxXY,ds.shape,frm.wxAxCtrlLst)
    imgPolar,theta,chi=frm.ai.xrpd2(ds[sl],frm.numPtTh,frm.numPtCh)
    if canvas.data.shape==imgPolar.shape:
      canvas.data[:]=imgPolar[:]
      glImg.data[:]=canvas.GetTxrData()
    else:
      canvas.data=imgPolar;
      glImg._data=canvas.GetTxrData()
      glImg._texture=Texture(glImg._data)
      #self.glImg=glImg=glumpy.image.Image(txrData, colormap=colMap,vmin=txrRng[0], vmax=txrRng[1])
      print canvas.data.shape,glImg.data.shape
    glImg.update()
    canvas.OnPaint(None)#force to repaint, Refresh and Update do not force !
    frm.Refresh(False)
    if event.GetId()==wx.ID_OK:
      event.Skip()#do not consume (use event to close the window and sent return code)
  
  
if __name__ == '__main__':
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):
    fnHDF='/scratch/detectorData/e14472_00033.hdf5'
    #lbl='mcs'
    lbl='pilatus_1'
    #lbl='spec'
    elem='/entry/data/'+lbl
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
      #frame = HdfPyFAIFrame(None,args.elem,hid)
      frame = HdfPyFAI1DFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
