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

#http://wxpython-users.1045709.n5.nabble.com/filling-a-wxgrid-td2348720.html
class Table1DArray(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    #ut.StopWatch.Log('DBG 1')
    self.data = data
    #ut.StopWatch.Log('DBG 2')
    #ut.StopWatch.Log('DBG 3')

  def GetRowLabelValue(self,idx):
    return idx
  
#  def GetColLabelValue(self,idx):
#    return 
  
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
    #ut.StopWatch.Log('DBG 1')
    self.data = data
    #ut.StopWatch.Log('DBG 2')
    #ut.StopWatch.Log('DBG 3')

  def GetRowLabelValue(self,idx):
    return idx
  
  def GetColLabelValue(self,idx):
    return idx
  
  def GetNumberRows(self):
    #ut.StopWatch.Log('GetNumberRows')
    return self.view.shape[0]

  def GetNumberCols(self):
    #ut.StopWatch.Log('GetNumberCols')
    return self.view.shape[1]

  def GetValue(self, row, col):
    #ut.StopWatch.Log('GetValue %d %d'%(row,col))
    return self.view[row,col]

class TableCompound(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    #ut.StopWatch.Log('DBG 1')
    self.data = data
    #ut.StopWatch.Log('DBG 2')
    #ut.StopWatch.Log('DBG 3')

  def GetRowLabelValue(self,idx):
    return idx
  
  def GetColLabelValue(self,idx):
    return self.view.dtype.names[idx]
  
  def GetNumberRows(self):
    #ut.StopWatch.Log('GetNumberRows')
    return self.view.shape[0]

  def GetNumberCols(self):
    #ut.StopWatch.Log('GetNumberCols')
    return self.view.dtype.num

  def GetValue(self, row, col):
    #ut.StopWatch.Log('GetValue %d %d'%(row,col))
    return self.view.value[row][col]

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
    #self.SetDefaultCellAlignment(wx.ALIGN_RIGHT,wx.ALIGN_CENTRE)
    self.SetDefaultCellAlignment(wx.ALIGN_CENTRE,wx.ALIGN_CENTRE)
   
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
    if t!=np.ndarray and type(hid.get_type())==h5py.h5t.TypeCompoundID:
      tbl = TableCompound(data)
      tbl.view = tbl.data
    else:
      wxAxCtrlLst=[]
      l=len(data.shape)
      if l==1:
        tbl = Table1DArray(data)
        tbl.view = tbl.data
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
    
        tbl = Table2DArray(data)
        tbl.idxXY=idxXY
        if idxXY[0]<idxXY[1]:
          tbl.view = tbl.data[sl]
        else:
          tbl.view = tbl.data[sl].T
      self.wxAxCtrlLst=wxAxCtrlLst
    grid.SetTable (tbl, True)   
       
    self.grid=grid

    pan.SetSizer(sizer)
    pan.Layout()
    self.Centre()
    
if __name__ == '__main__':
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
      frame = HdfGridFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
