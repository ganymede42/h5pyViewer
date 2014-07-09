#!/usr/bin/env python
#*-----------------------------------------------------------------------*
#|                                                                       |
#|  Copyright (c) 2013 by Paul Scherrer Institute (http://www.psi.ch)    |
#|                                                                       |
#|              Author Thierry Zamofing (thierry.zamofing@psi.ch)        |
#*-----------------------------------------------------------------------*
'''
implements a grid view classe to show 'excel-like'-tables of a hdf5 dataset.
'''

import wx,h5py,os
import wx.grid
import numpy as np
import utilities as ut

class DlgFormatSetup(wx.Dialog):
  def __init__(self,parent,fmt):
    wx.Dialog.__init__(self,parent,-1,'Format Setup')
    txtFmt=wx.StaticText(self,-1,'format')
    self.edFmt=edFmt=wx.TextCtrl(self,-1,fmt,style=wx.TE_PROCESS_ENTER)

    txtPredef=wx.StaticText(self,-1,'predefined')
    preDefLst=('default','0x%x','%f+%fi')
    self.cbPredef=cbPredef=wx.ComboBox(self, -1, choices=preDefLst, style=wx.CB_READONLY)
    #cbPredef.SetSelection(0)

    sizer=wx.BoxSizer(wx.VERTICAL)
    fgs=wx.FlexGridSizer(4,2,5,5)
    fgs.Add(txtFmt,0,wx.ALIGN_RIGHT)
    fgs.Add(edFmt,0,wx.EXPAND)
    fgs.Add(txtPredef,0,wx.ALIGN_RIGHT)
    fgs.Add(cbPredef,0,wx.EXPAND)
    sizer.Add(fgs,0,wx.EXPAND|wx.ALL,5)
    edFmt.SetFocus()
    btns =  self.CreateButtonSizer(wx.OK|wx.CANCEL)
    sizer.Add(btns,0,wx.EXPAND|wx.ALL,5)

    self.Bind(wx.EVT_COMBOBOX, self.OnModify, cbPredef)
    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnModify(self, event):
    #print 'OnModify'
    parent=self.GetParent()
    #event.EventObject.Value
    #self.cbPredef.Value
    if event.Int:
      self.edFmt.Value=event.GetString()
    else:
      self.edFmt.Value=''

#http://wxpython-users.1045709.n5.nabble.com/filling-a-wxgrid-td2348720.html
class Table1DArray(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    #ut.StopWatch.Log('DBG 1')
    self.data = data
    #ut.StopWatch.Log('DBG 2')

  def GetRowLabelValue(self,idx):
    return idx

  def GetColLabelValue(self,idx):
    return ''

  def GetNumberRows(self):
    #ut.StopWatch.Log('GetNumberRows')
    return self.data.shape[0]

  def GetNumberCols(self):
    #ut.StopWatch.Log('GetNumberCols')
    return 1

  def GetValue(self, row, col):
    #ut.StopWatch.Log('GetValue %d %d'%(row,col))
    return self.data[row]

class Table2DArray(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    self.data = data

  def GetRowLabelValue(self,idx):
    return idx

  def GetColLabelValue(self,idx):
    return idx

  def GetNumberRows(self):
    return self.view.shape[0]

  def GetNumberCols(self):
    return self.view.shape[1]

  def GetValue(self, row, col):
    try:
      return self.cellFormat%self.view[row][col]
    except AttributeError:
      return self.view[row][col]

class Table1DCompound(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    self.data = data

  def GetRowLabelValue(self,idx):
    return idx

  def GetColLabelValue(self,idx):
    return self.data.dtype.names[idx]

  def GetNumberRows(self):
    return self.data.shape[0]

  def GetNumberCols(self):
    return self.data.dtype.num

  def GetValue(self, row, col):
    try:
      return self.cellFormat%self.data[row][col]
    except AttributeError:
      return self.data[row][col]
  
class Table2DCompound(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    self.data = data

  def GetRowLabelValue(self,idx):
    return idx

  def GetColLabelValue(self,idx):
    return idx

  def GetNumberRows(self):
    return self.view.shape[0]

  def GetNumberCols(self):
    return self.view.shape[1]

  def GetValue(self, row, col):
    try:
      return self.cellFormat%self.view[row][col]
    except AttributeError:
      return self.view[row][col]

class Grid(wx.grid.Grid):
  def __init__(self, parent, data):
    wx.grid.Grid.__init__(self, parent, -1)

    self.SetDefaultColSize(50)
    self.SetDefaultRowSize(17)
    font=self.GetLabelFont()
    font.PointSize=8
    self.SetLabelFont(font)

    font=self.GetDefaultCellFont()
    font.PointSize=8
    self.SetDefaultCellFont(font)
    self.SetDefaultCellAlignment(wx.ALIGN_RIGHT,wx.ALIGN_CENTRE)
    #self.SetDefaultCellAlignment(wx.ALIGN_CENTRE,wx.ALIGN_CENTRE)
    #self.SetDefaultRenderer

  @staticmethod
  def OnSetView(usrData,value,msg):
    gridFrm =usrData.slider.Parent.Parent
    grid=gridFrm.grid
    tbl=grid.GetTable()
    data=tbl.data
    sl=ut.GetSlice(tbl.idxXY,data.shape,gridFrm.wxAxCtrlLst)

    #tbl.view = tbl.data[value,...]
    tbl.view = tbl.data[sl]
    grid.ClearGrid()
    pass

class HdfGridFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title='HDFGridView: '+lbl,size=wx.Size(750, 650))
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    pan = wx.Panel(self, -1)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      data=h5py.Dataset(hid)
    elif t==np.ndarray:
      data=hid
    else:
      raise(TypeError('unhandled type'))
    grid = Grid(pan, data)

    tbl=grid.GetTable()

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(grid, 1, wx.EXPAND)
    wxAxCtrlLst=[]
    l=len(data.shape)
    if l==1:
      if type(hid.get_type())==h5py.h5t.TypeCompoundID:
        tbl = Table1DCompound(data)
      else:
        tbl = Table1DArray(data)
    else:
      idxXY=(l-2,l-1)
      #idxXY=(l-1,l-2)
      for idx,l in enumerate(data.shape):
        if idx in idxXY:
          continue
        wxAxCtrl=ut.SliderGroup(pan, label='Axis:%d'%idx,range=(0,l-1))
        wxAxCtrl.idx=idx
        wxAxCtrlLst.append(wxAxCtrl)
        sizer.Add(wxAxCtrl.sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)
        wxAxCtrl.SetCallback(Grid.OnSetView,wxAxCtrl)

      sl=ut.GetSlice(idxXY,data.shape,wxAxCtrlLst)

      if type(hid.get_type())==h5py.h5t.TypeCompoundID:
        tbl = Table2DArray(data)
      else:
        tbl = Table2DArray(data)
      tbl.idxXY=idxXY
      if idxXY[0]<idxXY[1]:
        tbl.view = tbl.data[sl]
      else:
        tbl.view = tbl.data[sl].T
    self.wxAxCtrlLst=wxAxCtrlLst
    #print type(tbl)

    grid.SetTable (tbl, True)
    #AutoSize must be called after SetTable, but takes lot of time on big tables!
    if tbl.GetNumberCols()*tbl.GetNumberRows()<50*50:
      grid.AutoSizeColumns(True);grid.AutoSizeRows(True)
    #grid.SetDefaultColSize(200, True)       
    self.grid=grid

    pan.SetSizer(sizer)
    pan.Layout()
    self.Centre()
    self.BuildMenu()
    grid.Bind(wx.grid.EVT_GRID_CMD_COL_SIZE, self.OnColSize)


  def OnColSize(self,event):
    if event.ShiftDown():
      col=event.RowOrCol
      sz=self.grid.GetColSize(col)
      print 'OnColSize',col,sz
      self.grid.SetDefaultColSize(sz, True)   
      self.grid.ForceRefresh()    
    
  def OnSetFormat(self,event):
    print 'OnSetFormat'
    
    fmt=getattr(self.grid.Table,'cellFormat','')
    dlg=DlgFormatSetup(self,fmt)
    if dlg.ShowModal()==wx.ID_OK:
      tbl=self.grid.Table; v=dlg.edFmt.Value
      if v:
        tbl.cellFormat=v
      else:
        del tbl.cellFormat
      self.grid.ForceRefresh()    
    dlg.Destroy()    
    

  def BuildMenu(self):
    mnBar = wx.MenuBar()

    #-------- Edit Menu --------
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Setup Format', 'Setup the format of the cells');self.Bind(wx.EVT_MENU, self.OnSetFormat, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Invert X-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    self.mnIDxAxis=mnItem.GetId()
    #mnItem=mn.Append(wx.ID_ANY, 'Invert Y-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    #mnItem=mn.Append(wx.ID_ANY, 'Show Moments', 'Show image moments ', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnShowMoments, mnItem)
    #self.mnItemShowMoment=mnItem
    #mnItem=mn.Append(wx.ID_ANY, 'Tomo Normalize', 'Multiplies each pixel with a normalization factor. Assumes there exist an array exchange/data_white', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnTomoNormalize, mnItem)
    #self.mnItemTomoNormalize=mnItem
    mnBar.Append(mn, '&Edit')
    #mn = wx.Menu()
    #mnItem=mn.Append(wx.ID_ANY, 'Help', 'How to use the image viewer');self.Bind(wx.EVT_MENU, self.OnHelp, mnItem)
    #mnBar.Append(mn, '&Help')

    self.SetMenuBar(mnBar)
    self.CreateStatusBar()
    

if __name__ == '__main__':
  import os,sys,argparse #since python 2.7
  def GetParser():
    cmd='\n  ./'+os.path.basename(sys.argv[0])+' '
    exampleCmd=(('compound n*m','/scratch/detectorData/Ptychography/tst/initial_conditions_S01375.h5','objects/object_0'),
                ('compound n','/scratch/detectorData/e14472/scan_00033.hdf5','entry/data/spec'),
                ('array l*m*n','/scratch/detectorData/e14472/scan_00033.hdf5','entry/data/pilatus_1'),
                ('array n','/scratch/detectorData/e14472/scan_00033.hdf5','entry/data/pilatus_1_info'))

    epilog='Examples:'+''.join(map(lambda s:'\n # '+s[0]+' #'+cmd+'--hdfFile %s --elem %s'%s[1:],exampleCmd))
   
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__,
                                     epilog=epilog)
    parser.add_argument('--hdfFile', required=True, help='the hdf5 to show')
    parser.add_argument('--elem',    required=True,    help='the path to the element in the hdf5 file')
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
      frame = HdfGridFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
