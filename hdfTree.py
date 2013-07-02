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

class HdfAttrListCtrl(wx.ListCtrl):
  def __init__(self, parent, *args, **kwargs):
    wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT)#*args, **kwargs)
    self.InsertColumn(0, 'Name')
    self.InsertColumn(1, 'Value')
    self.InsertColumn(2, 'Type')
    self.SetColumnWidth(0, 140)
    self.SetColumnWidth(1, 440)
    self.SetColumnWidth(2, 160)
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
    for (idx,(k,v)) in enumerate(obj.attrs.iteritems()):
      self.InsertStringItem(idx, k)
      self.SetStringItem(idx, 1, str(v))
      self.SetStringItem(idx, 2, str(type(v)))

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
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(750, 350))
    self.wxLstCtrl=HdfAttrListCtrl(self)
    self.wxLstCtrl.ShowAttr(hid)  
    self.Centre()
 
 
class HdfImageFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(750, 350))
    #self.wxLstCtrl=HdfAttrListCtrl(self)
    #self.wxLstCtrl.ShowAttr(hid)  
    self.Centre()
 
class HdfTreePopupMenu(wx.Menu):
  def __init__(self, wxObjSrc):
    wx.Menu.__init__(self)
    self.wxObjSrc=wxObjSrc
    self.AddMenu(self.OnShowAttrib,"Show Attributes")
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

class HdfTree(wx.Frame):

  def Open(self,fnHDF):
    self.fid = h5py.h5f.open(fnHDF)
    self.wxTree.ShowHirarchy(self.fid)

  def Close(self):
    self.fid.close()
    del self.fid

  def __init__(self, parent, id, title):
    wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(650, 350))

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
           ('obj_track_times', h5py.h5p.PropDCID.get_obj_track_times),
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
  class MyApp(wx.App):
      def OnInit(self):
          frame = HdfTree(None, -1, 'hdfTree')
          frame.Open('/home/zamofing_t/Documents/prj/libDetXR/python/libDetXR/e14472_00033.hdf5')
          frame.Show(True)
          self.SetTopWindow(frame)
          return True
  
  app = MyApp(0)
  app.MainLoop()
