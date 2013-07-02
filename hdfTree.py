#!/usr/bin/python

# treectrl.py

import os
import wx,h5py

class HdfTreeCtrl(wx.TreeCtrl):
  def __init__(self, parent, *args, **kwargs):
    wx.TreeCtrl.__init__(self, parent, *args, **kwargs)
    il = wx.ImageList(16, 16)
    home    = il.Add(wx.Image("images/home.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
    folder  = il.Add(wx.Image("images/folder.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
    dataset = il.Add(wx.Image("images/dataset.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap())
    self.AssignImageList(il)

  def _ShowHirarchy(self,wxParent,gidParent,lvl):
    for gidStr in h5py.h5g.GroupIter(gidParent):
      gid = h5py.h5o.open(gidParent,gidStr)
      t=type(gid)
      if t==h5py.h5g.GroupID:
        image=1
      elif t==h5py.h5d.DatasetID:     
        image=2
      else:
        image=-1
      wxNode = self.AppendItem(wxParent, gidStr,image=image,data=wx.TreeItemData(gid))
      if t==h5py.h5g.GroupID:
        self._ShowHirarchy(wxNode,gid,lvl+1)

  def ShowHirarchy(self,hid):
    self.hid=hid
    t=type(hid)
    if t==h5py.h5f.FileID:
      txt=os.path.basename(hid.name)
    elif t==h5py.h5g.GroupID:
      txt=hid.name
    else:
      txt='root'
    wxNode = self.AddRoot(txt,image=0)
    self._ShowHirarchy(wxNode,hid,0)

    self.ExpandAll()

if __name__ == '__main__':
  class HdfTreeFrame(wx.Frame):
 
    def __init__(self, parent, id, title, fnHDF):
      wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(350, 450))
      wxTree = HdfTreeCtrl(self, 1, wx.DefaultPosition, (-1,-1),  wx.TR_HAS_BUTTONS)  
      self.Centre()
  
      fid = h5py.h5f.open(fnHDF)
      wxTree.ShowHirarchy(fid)
      self.wxTree=wxTree
      self.fid=fid

    def __del__(self):
      self.fid.close()

  
  class MyApp(wx.App):
    def OnInit(self):
      fnHDF='/home/zamofing_t/Documents/prj/libDetXR/python/libDetXR/e14472_00033.hdf5'
      frame = HdfTreeFrame(None, -1, 'hdfTree',fnHDF)
      frame.Show(True)
      self.SetTopWindow(frame)
      return True
  
  app = MyApp(0)
  app.MainLoop()
