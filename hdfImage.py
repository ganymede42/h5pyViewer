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
#or from matplotlib.backends.backend_wx import FigureCanvasWx as FigureCanvas

class HdfImageFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(750, 350))

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      data=h5py.Dataset(hid)


    fig = mpl.figure.Figure()
    #ax = fig.add_subplot(111)
    #ax = fig.add_axes([0.075,0.1,0.75,0.85])
    ax = fig.add_axes([0.075,0.1,0.75,0.85])
    #cax = self.fig.add_axes([0.85,0.1,0.075,0.85])

    #img = ax.imshow(np.random.rand(10,10),interpolation='nearest')
    canvas = FigureCanvas(self, -1, fig)
    canvas.mpl_connect('motion_notify_event', self.OnMotion)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
    self.SetSizer(sizer)

    #self.fig=fig
    toolbar=ut.AddToolbar(canvas,sizer)  
    statusBar = wx.StatusBar(self, -1)
    statusBar.SetFieldsCount(1)
    sizer.Add(statusBar, 0, wx.LEFT | wx.EXPAND)

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
    img = ax.imshow(data[sl],interpolation='nearest',cmap=mpl.cm.jet, vmin=0, vmax=10)
    fig.colorbar(img,orientation='vertical')
      
    self.Fit()   
    self.Centre()
    
    self.ax=ax
    self.img=img
    self.canvas=canvas
    self.sizer=sizer
    self.toolbar=toolbar
    self.statusBar=statusBar
    self.data=data
    self.idxXY=idxXY
    self.wxAxCtrlLst=wxAxCtrlLst
  
  def SetIdxXY(self,x,y):
    self.idxXY=(x,y)
 
  @staticmethod
  def OnSetView(usrData,value,msg):
    imgFrm=usrData.slider.Parent
    #imgFrm.img.set_array(imgFrm.data[usrData.value,...])
    data=imgFrm.data
    sl=ut.GetSlice(imgFrm.idxXY,data.shape,imgFrm.wxAxCtrlLst)
    imgFrm.img.set_array(data[sl])
    imgFrm.canvas.draw()
    pass
    
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
        self.statusBar.SetStatusText( "x= %d y=%d val=%g"%(x,y,v),0)

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
