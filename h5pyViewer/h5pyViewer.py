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
import wx.py
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
    self.AddMenu(self.OnShell,"Python Shell")
    self.AddMenu(self.OnItem1,"Item One")
    self.AddMenu(self.OnItem2,"Item Two")
    self.AddMenu(self.OnItem3,"Item Three")

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
    
  def OnShell(self, event):
    wxTree,wxNode=self.wxObjSrc
    frame = wx.Frame(wxTree, -1, "wxPyShell",size=wx.Size(800, 500))
    frame.Centre()
    wnd=app.GetTopWindow() 
    loc={'app'  :app,
         'fid'  :app.GetTopWindow().fid,
         'lbl'  :wxTree.GetItemText(wxNode),
         'hid'  :wxTree.GetPyData(wxNode),
         'h5py' : h5py
         }
    introText='''Shell to the HDF5 objects
app: application object
fid: hdf5 file object
lbl: label of selected hdf5 object
hid: selected hdf5 object

Example:
import h5py
ds=h5py.Dataset(hid)
ds
ds[1,:,:]
'''
    shell=wx.py.shell.Shell(frame, introText=introText,locals=loc)
    frame.Show(True)
    #if loc is None, all variables are visible. the context is global
    #shell.push('wnd=app.GetTopWindow()')
    #for cmd in [
    #  'wnd=app.GetTopWindow();wxTree=wnd.wxTree',
    #  'wxNode=wnd.wxTree.GetSelection()',
    #  'print wnd.fid',
    #  'lbl=wxTree.GetItemText(wxNode)',
    #  'hid=wxTree.GetPyData(wxNode)']:
    #  shell.run(cmd, prompt=False)

  def OnItem1(self, event):
    print "Item One selected obj %s"%self.lbl
  def OnItem2(self, event):
    print "Item Two selected obj %s"%self.lbl
  def OnItem3(self, event):
    print "Item Three selected obj %s"%self.lbl

class HdfViewerFrame(wx.Frame):

  def OpenFile(self,fnHDF):
    try:
      self.fid=h5py.h5f.open(fnHDF)
    except IOError as e:
      sys.stderr.write('Unable to open File: '+fnHDF+'\n')
    else: 
      self.wxTree.ShowHirarchy(self.fid)

  def CloseFile(self):
    #http://docs.wxwidgets.org/2.8/wx_windowdeletionoverview.html#windowdeletionoverview
    print 'CloseFile'
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
    self.BuildMenu()
    
    self.Centre()

    self.wxTree=wxTree
    self.display=wxTxt
  def __del__(self):
    self.CloseFile()
  
  def OnOpen(self, event):
    dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), '','HDF5 files (*.hdf5)|*.hdf5|all (*.*)|*.*', wx.OPEN|wx.FD_CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
      path = dlg.GetPath()
      #mypath = os.path.basename(path)
      #self.SetStatusText("You selected: %s" % mypath)
      self.CloseFile()
      self.OpenFile(path)
      print 'OnOpen',path
    dlg.Destroy()       
  
  def OnCloseWindow(self, event):
    print 'OnCloseWindow'
    self.Destroy()
    
  def BuildMenu(self):
    #http://wiki.wxpython.org/AnotherTutorial#wx.MenuBar
    mnBar = wx.MenuBar()

    #-------- File Menu --------
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_OPEN, '&Open', 'Open a new document');self.Bind(wx.EVT_MENU, self.OnOpen, mnItem)
    mnSub = wx.Menu()
    mnItem=mnSub.Append(wx.ID_ANY, 'SubMenuEntry', 'My SubMenuEntry')
    mn.AppendMenu(wx.ID_ANY, 'SubMenu', mnSub)   
    mn.AppendSeparator()
    mnItem=mn.Append(wx.ID_EXIT, '&Quit', 'Quit the Application');self.Bind(wx.EVT_MENU, self.OnCloseWindow, mnItem)
    mnBar.Append(mn, '&File')
    
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    #-------- Edit Menu --------
    mn = wx.Menu()
    mnBar.Append(mn, '&Edit')

    #-------- Help Menu --------
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_HELP,'Help','Application Help')
    mnItem=mn.Append(wx.ID_ABOUT,'About','Application About')
    mnBar.Append(mn, '&Help')
          
    #mn.AppendSeparator()
    #mnItem = wx.MenuItem(mn, 105, '&Quit\tCtrl+Q', 'Quit the Application')
    #mnItem.SetBitmap(wx.Image('stock_exit-16.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap())
    #mn.AppendItem(mnItem)   
    self.SetMenuBar(mnBar)
    self.CreateStatusBar()   

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
      frame.OpenFile(args.hdfFile)
      frame.Show(True)
      self.SetTopWindow(frame)
      return True
    
#------------------ Main Code ----------------------------------    
  app = MyApp()
  app.MainLoop()
