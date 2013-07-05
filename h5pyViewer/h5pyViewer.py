#!/usr/bin/env python
#*-----------------------------------------------------------------------*
#|                                                                       |
#|  Copyright (c) 2013 by Paul Scherrer Institute (http://www.psi.ch)    |
#|                                                                       |
#|              Author Thierry Zamofing (thierry.zamofing@psi.ch)        |
#*-----------------------------------------------------------------------*
'''
hdf5 viewer to dispay images, tables, attributes and trees of a hdf5 file.
'''
import os,sys
import wx,h5py
from hdfTree import *
from hdfGrid import *
from hdfAttrib import *
from hdfImage import  *

class HdfTreePopupMenu(wx.Menu):
  def __init__(self, wxObjSrc):
    wx.Menu.__init__(self)
    self.wxObjSrc=wxObjSrc
    self.AddMenu(self.OnShowAttrib,"Show Attributes")
    self.AddMenu(self.OnShowData,"Show Data")
    self.AddMenu(self.OnShowImage,"Show Image")
    self.AddMenu(self.OnItem1,"Item One")
    self.AddMenu(self.OnItem2,"Item Two")
    self.AddMenu(self.OnItem2,"Item Three")

  def AddMenu(self,func,lbl):
    item = wx.MenuItem(self, -1, lbl)
    self.AppendItem(item);
    self.Bind(wx.EVT_MENU, func, item)
    return item
    
  def OnShowAttrib(self, event):
    wxTree,wxNode=self.wxObjSrc
    lbl=wxTree.GetItemText(wxNode)
    hid=wxTree.GetPyData(wxNode)
    frame=HdfAttribFrame(wxTree,lbl,hid)
    frame.Show(True)
    
    
  def OnShowData(self, event):
    wxTree,wxNode=self.wxObjSrc
    lbl=wxTree.GetItemText(wxNode)
    hid=wxTree.GetPyData(wxNode)
    frame=HdfGridFrame(wxTree,lbl,hid)
    frame.Show(True)  

  def OnShowImage(self, event):
    wxTree,wxNode=self.wxObjSrc
    lbl=wxTree.GetItemText(wxNode)
    hid=wxTree.GetPyData(wxNode)
    frame=HdfImageFrame(wxTree,lbl,hid)
    frame.Show(True)  
    
  def OnItem1(self, event):
    print "Item One selected obj %s"%self.lbl
  def OnItem2(self, event):
    print "Item Two selected obj %s"%self.lbl
  def OnItem3(self, event):
    print "Item Three selected obj %s"%self.lbl

class HdfViewerFrame(wx.Frame):

  def Open(self,fnHDF):
    try:
      self.fid=h5py.h5f.open(fnHDF)
    except IOError as e:
      sys.stderr.write('Unable to open File: '+fnHDF+'\n')
    else: 
      self.wxTree.ShowHirarchy(self.fid)

  def Close(self):
    try:
      self.fid.close()
      del self.fid
    except AttributeError as e:
      pass

  def __init__(self, parent, title):
    wx.Frame.__init__(self, parent, title=title, size=wx.Size(650, 350))

    wxSplt = wx.SplitterWindow(self, -1)
    wxTree = HdfTreeCtrl(wxSplt, 1, wx.DefaultPosition, (-1,-1),  wx.TR_HAS_BUTTONS)
    wxTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, id=1)
    wxTree.Bind(wx.EVT_TREE_ITEM_MENU, self.OnMenu, id=1)
    #wx.EVT_TREE_ITEM_MENU(id, func)
    wxTxt = wx.StaticText(wxSplt, -1, '',(10,10) )#, style=wx.ALIGN_CENTRE)

    wxSplt.SplitVertically(wxTree, wxTxt)

    #wxLstCtrl=HdfAttrListCtrl(wxSplt)
    #wxSplt.SplitVertically(wxTree, wxLstCtrl)

    
    self.Centre()

    self.wxTree=wxTree
    self.display=wxTxt
  def __del__(self):
    self.Close()   

  def OnSelChanged(self, event):
      wxTree=self.wxTree
      wxNode =  event.GetItem()
      txt=wxTree.GetItemText(wxNode)
      data=wxTree.GetPyData(wxNode)
      #o=wxTree.GetItemData(wxNode)
      #print o.Data,wxTree.GetPyData(wxNode)
      #if type(gid)==h5py.h5g.GroupID:
      if data:
        t=type(data)
        if t==h5py.h5g.GroupID:
          pass
        elif t==h5py.h5d.DatasetID:
          l=[txt]
          l.append('shape: '+str(data.shape))
          tt=data.get_type()
          if type(tt)==h5py.h5t.TypeCompoundID:
            l.append('type: Compound')
          else:
            l.append('type: '+str(tt.dtype))
          
          pl=data.get_create_plist()
          txFcn=(
           ('chunk',h5py.h5p.PropDCID.get_chunk),
           ('fill time',h5py.h5p.PropDCID.get_fill_time),
           ('alloc_time',  h5py.h5p.PropDCID.get_alloc_time),
           #('class',       h5py.h5p.PropDCID.get_class),
           ('fill_time',   h5py.h5p.PropDCID.get_fill_time),
           #('fill_value',  h5py.h5p.PropDCID.get_fill_value),
           #('filter',      h5py.h5p.PropDCID.get_filter),
           #('filter_by_id',h5py.h5p.PropDCID.get_filter_by_id),
           ('layout',      h5py.h5p.PropDCID.get_layout),
           ('nfilters',    h5py.h5p.PropDCID.get_nfilters),
           #('obj_track_times', h5py.h5p.PropDCID.get_obj_track_times),
           )
          for tx,func in txFcn:
            try: v=func(pl)
            except ValueError as e: pass
            else: l.append(tx+': '+str(v))
                    
          txt='\n'.join(l)
        print t,data.id
      self.display.SetLabel(txt)

  def OnMenu(self, event):
      wxNode =  event.GetItem()
      self.PopupMenu(HdfTreePopupMenu((self.wxTree,wxNode)), event.GetPoint())    

if __name__ == '__main__':
  def GetArgs():   
    import sys,argparse #since python 2.7
    fnHDF='/scratch/detectorData/e14472_00033.hdf5'

    exampleCmd='--hdfFile='+fnHDF    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__,
                                     epilog='Example:\n'+os.path.basename(sys.argv[0])+' '+exampleCmd+'\n ')
    parser.add_argument('--hdfFile', default=fnHDF, help='the hdf5 to show')
    
    args = parser.parse_args()
    return args

  class MyApp(wx.App):
    def OnInit(self):
      args=GetArgs()
      frame = HdfViewerFrame(None, 'h5pyViewer')
      frame.Open(args.hdfFile)
      frame.Show(True)
      self.SetTopWindow(frame)
      return True
    
#------------------ Main Code ----------------------------------    
  app = MyApp()
  app.MainLoop()
