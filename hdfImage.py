#!/usr/bin/env python
"""
An example of how to use wx or wxagg in an application with the new
toolbar - comment out the setA_toolbar line for no toolbar
"""

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
      obj=h5py.Dataset(hid)


    fig = mpl.figure.Figure()
    #ax = fig.add_subplot(111)
    #ax = fig.add_axes([0.075,0.1,0.75,0.85])
    ax = fig.add_axes([0.075,0.1,0.75,0.85])
    #cax = self.fig.add_axes([0.85,0.1,0.075,0.85])

    #img = ax.imshow(np.random.rand(10,10),interpolation='nearest')
    img = ax.imshow(obj[1,...],interpolation='nearest',cmap=mpl.cm.jet, vmin=0, vmax=10)
    fig.colorbar(img,orientation='vertical')
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

    wxAxCtrl=ut.SliderGroup(self, label='Axis:%d'%0)
    sizer.Add(wxAxCtrl.sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)
    wxAxCtrl.SetCallback(HdfImageFrame.SetSlice,self)

    self.Fit()   
    self.Centre()
    
    self.ax=ax
    self.img=img
    self.canvas=canvas
    self.sizer=sizer
    self.toolbar=toolbar
    self.statusBar=statusBar
    self.data=obj
  
  @staticmethod
  def SetSlice(usrData,value,msg):
    #usrData.img.set_data(usrData.data[value,...])
    usrData.img.set_array(usrData.data[value,...])
    usrData.canvas.draw()
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
  class App(wx.App):
    def OnInit(self):
      fnHDF='/home/zamofing_t/Documents/prj/libDetXR/python/libDetXR/e14472_00033.hdf5'
      lbl='mcs'
      lbl='pilatus_1'
      fid = h5py.h5f.open(fnHDF)
      hid = h5py.h5o.open(fid,'/entry/dataScan00033/'+lbl)
      frame = HdfImageFrame(None,lbl,hid)
      frame.Show()
      return True
  
  app = App()
  app.MainLoop()
