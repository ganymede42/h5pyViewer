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
from GLCanvasImg import *
  
class HdfImageGLFrame(wx.Frame):
  def __init__(self, parent, title, hid):
        # Forcing a specific style on the window.
        #   Should this include styles passed?
    style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
    wx.Frame.__init__(self, parent, title=title, size=wx.Size(850, 650), style=style)
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)
    canvas=GLCanvasImg(self,self.SetStatusCB)

    t = type(hid)
    if t == h5py.h5d.DatasetID:
      ds = h5py.Dataset(hid)
      self.dataSet=ds

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
    self.SetSizer(sizer)

    wxAxCtrlLst=[]
    l=len(ds.shape)
    idxXY=(l-2,l-1)
    for idx,l in enumerate(ds.shape):
      if idx in idxXY:
        continue 
      wxAxCtrl=ut.SliderGroup(self, label='Axis:%d'%idx,range=(0,l-1))
      wxAxCtrl.idx=idx
      wxAxCtrlLst.append(wxAxCtrl)
      sizer.Add(wxAxCtrl.sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)
      wxAxCtrl.SetCallback(self.OnSetView,wxAxCtrl)

    sl=ut.GetSlice(idxXY,ds.shape,wxAxCtrlLst)
    

    canvas.data=ds[sl]
      
    #self.Fit()   
    self.Centre()
    
    self.canvas=canvas
    self.sizer=sizer
    self.idxXY=idxXY
    self.wxAxCtrlLst=wxAxCtrlLst
    self.BuildMenu()

  def BuildMenu(self):
    mnBar = wx.MenuBar()

    #-------- Edit Menu --------
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Setup Colormap', 'Setup the color mapping ');self.Bind(wx.EVT_MENU, self.canvas.OnColmapSetup, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Linear Mapping', 'Use a linear values to color mapping ');self.Bind(wx.EVT_MENU, self.OnMapLin, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Log Mapping', 'Use a logarithmic values to color mapping ');self.Bind(wx.EVT_MENU, self.OnMapLog, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Invert X-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    #self.mnIDxAxis=mnItem.GetId()
    #mnItem=mn.Append(wx.ID_ANY, 'Invert Y-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    mnBar.Append(mn, '&Edit')
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Help', 'How to use the image viewer');self.Bind(wx.EVT_MENU, self.canvas.OnHelp, mnItem)
    mnBar.Append(mn, '&Help')

    self.SetMenuBar(mnBar)
    self.CreateStatusBar()      

  @staticmethod
  def SetStatusCB(obj,mode,v):
    if mode==0:
      obj.SetStatusText( "Pos:(%d,%d) Value:%d"%v,0)

  @staticmethod
  def OnSetView(usrData,value,msg):
    'called when a slice is selected with the slider controls'
    frm=usrData.slider.Parent
    ds=frm.dataSet
    canvas=frm.canvas
    glImg=canvas.glImg
    sl=ut.GetSlice(frm.idxXY,ds.shape,frm.wxAxCtrlLst)
    canvas.data[:]=ds[sl][:]
    glImg.data[:]=canvas.GetTxrData()
    glImg.update()
    canvas.OnPaint(None)#force to repaint, Refresh and Update do not force !
    #canvas.Refresh(False)
    #canvas.Update()
    pass

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
      frame = HdfImageGLFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
