import os
import wx,h5py
import numpy as np

class HdfAttrListCtrl(wx.ListCtrl):
  def __init__(self, parent, *args, **kwargs):
    wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT)#*args, **kwargs)
    self.InsertColumn(0, 'Name')
    self.InsertColumn(1, 'Value')
    self.InsertColumn(2, 'Unit')
    self.InsertColumn(3, 'Type')
    self.SetColumnWidth(0, 140)
    self.SetColumnWidth(1, 440)
    self.SetColumnWidth(2, 60)
    self.SetColumnWidth(3, 160)
  def ShowAttr(self,hid):
    self.hid=hid
    t=type(hid)
    if t==h5py.h5d.DatasetID:
      obj=h5py.Dataset(hid)
    elif t==h5py.h5g.GroupID:
      obj=h5py.Group(hid)
    else:
      raise(BaseException('cant handle'))
    self.DeleteAllItems()
    idx=0
    for (k,v) in obj.attrs.iteritems():
      if k.startswith('_u_'):
        continue
      self.InsertStringItem(idx, k)
      self.SetStringItem(idx, 1, str(v))
      try:
        unit=obj.attrs['_u_'+k]
      except KeyError as e:
        pass
      else:
        self.SetStringItem(idx, 2, unit)
      t=type(v)
      if t==np.ndarray:
        tStr=str(v.dtype)+str(v.shape)
        if tStr[-2]==',':
          tStr=tStr[:-2]+')'
      else:
        tStr=type(v).__name__
        try: tStr+='(%d)'%len(v)
        except TypeError as e: pass
      self.SetStringItem(idx, 3, tStr)
      idx+=1

    #print h5py.h5a.get_num_attrs(hid)
    #def iterCallback(name, *args):
      #print name, args
      #attr = h5py.h5a.open(hid, name)
      #t=type(attr)
      #tid = attr.get_type()
      #rtdt = h5py.Dataset.readtime_dtype(attr.dtype, [])   
      #arr = np.ndarray(attr.shape, dtype=rtdt, order='C')
      #attr.read(arr)
    #h5py.h5a.iterate(hid, iterCallback)
    pass

class HdfAttribFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(800, 350))
    self.wxLstCtrl=HdfAttrListCtrl(self)
    self.wxLstCtrl.ShowAttr(hid)  
    self.Centre()
 
if __name__ == '__main__':
  class MyApp(wx.App):
    def OnInit(self):
      fnHDF='/home/zamofing_t/Documents/prj/libDetXR/python/libDetXR/e14472_00033.hdf5'
      fid = h5py.h5f.open(fnHDF)
      hid = h5py.h5o.open(fid,'/entry/dataScan00033/mcs')
      frame = HdfAttribFrame(None, 'HdfAttribFrame',hid)
      frame.Show(True)
      self.SetTopWindow(frame)
      self.fid=fid
      return True
  
    def OnExit(self):
      self.fid.close()

      
  app = MyApp(0)
  app.MainLoop()