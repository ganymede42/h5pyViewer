#!/usr/bin/env python
#*-----------------------------------------------------------------------*
#|                                                                       |
#|  Copyright (c) 2013 by Paul Scherrer Institute (http://www.psi.ch)    |
#|                                                                       |
#|              Author Thierry Zamofing (thierry.zamofing@psi.ch)        |
#*-----------------------------------------------------------------------*
'''
hdf5 tree viewer to dispay the tree of a hdf5 file.
'''

import os
import wx,h5py

class HdfTreeCtrl(wx.TreeCtrl):
  def __init__(self, parent, *args, **kwargs):
    wx.TreeCtrl.__init__(self, parent, *args, **kwargs)
    il = wx.ImageList(16, 16)
    rootDir=os.path.join(os.path.dirname(__file__),'images')
    for img in ('home','folder','dataset','compound','text'):
      il.Add(wx.Image(rootDir+'/%s.png'%img, wx.BITMAP_TYPE_PNG).ConvertToBitmap())
    self.AssignImageList(il)

  def _ShowHirarchy(self,wxParent,gid,lvl):
    #numObj=gid.get_num_objs()
    #for idx in range(numObj):
    #  hidStr=get_objname_by_idx(idx)
    #  get_objtype_by_idx(INT idx)
    for hidStr in h5py.h5g.GroupIter(gid):
      hid = h5py.h5o.open(gid,hidStr)
      #try:
      #  gid.get_linkval(hidStr)
      #except BaseException as e:
      #  pass
      #else:
      #  print hidStr,'is a sym link'
      t=type(hid)
      if t==h5py.h5g.GroupID:
        image=1
      elif t==h5py.h5d.DatasetID:
        tt=type(hid.get_type())
        if tt==h5py.h5t.TypeCompoundID:
          image=3
        elif tt==h5py.h5t.TypeStringID:
          image=4
        else:
          image=2
      else:
        image=-1
      wxNode = self.AppendItem(wxParent, hidStr,image=image,data=wx.TreeItemData(hid))
      if t==h5py.h5g.GroupID:
        self._ShowHirarchy(wxNode,hid,lvl+1)

  def ShowHirarchy(self,hid):
    self.hid=hid
    t=type(hid)
    if t==h5py.h5f.FileID:
      txt=os.path.basename(hid.name)
    elif t==h5py.h5g.GroupID:
      txt=hid.name
    else:
      txt='root'
    self.DeleteAllItems()
    wxNode = self.AddRoot(txt,image=0,data=wx.TreeItemData(hid))
    self._ShowHirarchy(wxNode,hid,0)

    #self.ExpandAll()
    self.ExpandLvl(wxNode,3)

  def ExpandLvl(self,wxNode,lvl):
    #print lvl,self.GetItemText(wxNode)
    self.Expand(wxNode)
    lvl=lvl-1
    if lvl==0:
      return
    wxCld,cookie=self.GetFirstChild(wxNode)
    while True:
      if not wxCld.IsOk():
        break
      self.ExpandLvl(wxCld,lvl)
      wxCld,cookie=self.GetNextChild(wxNode,cookie)

if __name__ == '__main__':
  import utilities as ut
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):   
    fnHDF='/scratch/detectorData/e14472_00033.hdf5'
    #lbl='mcs'
    #lbl='pilatus_1'
    lbl='spec'
    exampleCmd='--hdfFile='+fnHDF
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__,
                                     epilog='Example:\n'+os.path.basename(sys.argv[0])+' '+exampleCmd+'\n ')
    parser.add_argument('--hdfFile', required=required, default=fnHDF, help='the hdf5 to show')
    return parser
    args = parser.parse_args()
    return args

  class HdfTreeFrame(wx.Frame):
 
    def __init__(self, parent, title, fid):
      wx.Frame.__init__(self, parent, title=title, size=wx.Size(350, 450))
      wxTree = HdfTreeCtrl(self, style=wx.TR_HAS_BUTTONS)  
      self.Centre()
      wxTree.ShowHirarchy(fid)
      self.wxTree=wxTree
      self.fid=fid

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
      frame = HdfTreeFrame(None,args.hdfFile,fid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
