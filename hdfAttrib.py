#!/usr/bin/env python
#*-----------------------------------------------------------------------*
#|                                                                       |
#|  Copyright (c) 2013 by Paul Scherrer Institute (http://www.psi.ch)    |
#|                                                                       |
#|              Author Thierry Zamofing (thierry.zamofing@psi.ch)        |
#*-----------------------------------------------------------------------*
'''
implements an attribute view of a hdf5 dataset.
'''

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
  import utilities as ut
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):   
    fnHDF='/scratch/detectorData/e14472_00033.hdf5'
    #lbl='mcs'
    #lbl='pilatus_1'
    lbl='spec'
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
      frame = HdfAttribFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
