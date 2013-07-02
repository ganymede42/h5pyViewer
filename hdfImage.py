import os
import wx,h5py


class HdfImageFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(750, 350))
    #self.wxLstCtrl=HdfAttrListCtrl(self)
    #self.wxLstCtrl.ShowAttr(hid)  
    self.Centre()
 