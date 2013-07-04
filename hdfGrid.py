
import wx,h5py
import wx.grid
import numpy as N
import utilities as ut
import time
#http://wxpython-users.1045709.n5.nabble.com/filling-a-wxgrid-td2348720.html

class StopWatch():
  @classmethod
  def Start(cls):
    cls.ts=time.time()
  @classmethod
  def Log(cls,str=None,restart=True):
    ts=time.time()
    print '%.6f'%(ts-cls.ts),str
    if restart:
      cls.ts=ts

class Table2DArray(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    #StopWatch.Log('DBG 1')
    self.data = data
    #StopWatch.Log('DBG 2')
    #StopWatch.Log('DBG 3')

  #def GetRowLabelValue(self,idx):
  #  return idx
  def GetColLabelValue(self,idx):
    return idx
  
  def GetNumberRows(self):
    #StopWatch.Log('GetNumberRows')
    return self.view.shape[0]

  def GetNumberCols(self):
    #StopWatch.Log('GetNumberCols')
    return self.view.shape[1]

  def GetValue(self, row, col):
    #StopWatch.Log('GetValue %d %d'%(row,col))
    return self.view[row,col]

class TableCompound(wx.grid.PyGridTableBase):
  def __init__(self, data):
    wx.grid.PyGridTableBase.__init__(self)
    #StopWatch.Log('DBG 1')
    self.data = data
    #StopWatch.Log('DBG 2')
    #StopWatch.Log('DBG 3')

  #def GetRowLabelValue(self,idx):
  #  return idx
  def GetColLabelValue(self,idx):
    return self.view.dtype.names[idx]
  
  def GetNumberRows(self):
    #StopWatch.Log('GetNumberRows')
    return self.view.shape[0]

  def GetNumberCols(self):
    #StopWatch.Log('GetNumberCols')
    return self.view.dtype.num

  def GetValue(self, row, col):
    #StopWatch.Log('GetValue %d %d'%(row,col))
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

    pan = wx.Panel(self, -1)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      data=h5py.Dataset(hid)
    #StopWatch.Log('DBG 0.1')
    #obj=N.random.rand(2,3000,4000)
    #data=obj.value
    #shape=obj.value.shape
    #StopWatch.Log('DBG 0.2')
    #grid = Grid(pan, N.random.rand(3000,4000))
    grid = Grid(pan, data)
    
    tbl=grid.GetTable()

      
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(grid, 1, wx.EXPAND)

    if type(hid.get_type())==h5py.h5t.TypeCompoundID:
      tbl = TableCompound(data)
      tbl.view = tbl.data
    else:
      wxAxCtrlLst=[]
      l=len(data.shape)
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
  class App(wx.App):
    def OnInit(self):
      fnHDF='/home/zamofing_t/Documents/prj/libDetXR/python/libDetXR/e14472_00033.hdf5'
      lbl='mcs'
      lbl='pilatus_1'
      lbl='spec'
      fid = h5py.h5f.open(fnHDF)
      hid = h5py.h5o.open(fid,'/entry/dataScan00033/'+lbl)
      frame = HdfGridFrame(None,lbl,hid)
      frame.Show()
      return True
  StopWatch.Start()
  app = App()
  app.MainLoop()
