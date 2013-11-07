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
from hdfGrid import *

def GetAttrVal(aid):
  rtdt = h5py._hl.dataset.readtime_dtype(aid.dtype, []) 
  arr = np.ndarray(aid.shape, dtype=rtdt, order='C')
  aid.read(arr)
  if len(arr.shape) == 0:
    return arr[()]
  return arr

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
    self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivateItem, self)
    
  def ShowAttr(self,hid):
    self.hid=hid
    self.DeleteAllItems()
    numAttr=h5py.h5a.get_num_attrs(hid)

    for idxAttr in range(numAttr):
      aid=h5py.h5a.open(hid,index=idxAttr)
      if aid.name.startswith('_u_'):
        continue
      idxItem=self.InsertStringItem(idxAttr, aid.name)
      val=GetAttrVal(aid)
      self.SetStringItem(idxItem, 1, str(val))
      #print idxAttr,idxItem,aid,aid.name,val
      try:
        aidUnit=h5py.h5a.open(hid,'_u_'+aid.name)
      except KeyError as e:
        pass
      else:
        unit=GetAttrVal(aidUnit)
        self.SetStringItem(idxItem, 2, unit)  
      t=type(val)
      if t==np.ndarray:
        tStr=str(val.dtype)+str(val.shape)
        if tStr[-2]==',':
          tStr=tStr[:-2]+')'
      else:
        tStr=type(val).__name__
        try: tStr+='(%d)'%len(val)
        except TypeError as e: pass
      self.SetStringItem(idxItem, 3, tStr)
      #http://wiki.wxpython.org/ListControls
      #only intergers can be associate
      self.SetItemData(idxItem, idxAttr)    

  def OnActivateItem(self,event):
    hid=self.hid
    aid=h5py.h5a.open(hid,index=event.Data)
    val=GetAttrVal(aid)
    if type(val)!=np.ndarray:
      print val
      return    
    frame=HdfGridFrame(self,aid.name,val)
    frame.Show(True)  

class HdfAttribFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(800, 350))
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)
    self.wxLstCtrl=HdfAttrListCtrl(self)  
    self.wxLstCtrl.ShowAttr(hid)  
    self.Centre()
 
if __name__ == '__main__':
  import utilities as ut
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):   
    fnHDF='/scratch/detectorData/e14472/scan_00030-00033.hdf5'
    #lbl='mcs'
    #lbl='pilatus_1'
    lbl='spec'
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
      frame = HdfAttribFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
