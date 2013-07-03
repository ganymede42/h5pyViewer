
import wx,h5py
import wx.grid
import numpy as N
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


class SliderGroup():
    def __init__(self, parent, label, range=(0,100),cbFuncData=None):
        self.sliderLabel = wx.StaticText(parent, label=label)
        self.sliderText = wx.TextCtrl(parent, -1, style=wx.TE_PROCESS_ENTER)
        self.slider = wx.Slider(parent, -1)
        self.slider.SetRange(range[0],range[1])      
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sliderLabel, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=2)
        sizer.Add(self.sliderText, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=2)
        sizer.Add(self.slider, 1, wx.EXPAND)
        self.sizer = sizer
        self.slider.Bind(wx.EVT_SLIDER, self.sliderHandler)
        self.sliderText.Bind(wx.EVT_TEXT_ENTER, self.sliderTextHandler)
        self.cbFuncData=cbFuncData
        self.txtFmt='%d'
        self.value=None

    def sliderHandler(self, evt):
        value = evt.GetInt()
        self.sliderText.SetValue(self.txtFmt%value)
        self.value=value
        if self.cbFuncData:
          self.cbFuncData[0](0,self.cbFuncData[1],value)
        
    def sliderTextHandler(self, evt):
        value = int(self.sliderText.GetValue())
        self.slider.SetValue(value)
        value = self.slider.Value
        self.sliderText.SetValue(self.txtFmt%value)
        self.value=value
        if self.cbFuncData:
          self.cbFuncData[0](1,self.cbFuncData[1],value)
        
class TableBase(wx.grid.PyGridTableBase):
    def __init__(self, data):
        wx.grid.PyGridTableBase.__init__(self)
        #StopWatch.Log('DBG 1')
        self.data = data
        #StopWatch.Log('DBG 2')
        self.view = data[0,...]
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

    table = TableBase(data)
    self.SetTable (table, True)
    
    #self.SetDefaultRenderer

  @staticmethod
  def OnChangeAxVal(idx,args,val):
    tbl=args.GetTable()
    tbl.view = tbl.data[val,...]
    args.ClearGrid()
    pass

class HdfGridFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title='HDFGridView: '+lbl,size=wx.Size(750, 650))

    pan = wx.Panel(self, -1)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      obj=h5py.Dataset(hid)
    #StopWatch.Log('DBG 0.1')
    #obj=N.random.rand(2,3000,4000)
    #data=obj.value
    #shape=obj.value.shape
    #StopWatch.Log('DBG 0.2')
    #grid = Grid(pan, N.random.rand(3000,4000))
    self.grid = Grid(pan, obj)      
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.grid, 1, wx.EXPAND)
    idxRowCol=(1,2)
    ctrlAxis=[]
    for idx in range(len(obj.shape)-2):
      wxAxCtrl=SliderGroup(pan, label='Axis:%d'%idx,cbFuncData=(Grid.OnChangeAxVal,(self.grid)))
      ctrlAxis.append(wxAxCtrl)
      sizer.Add(wxAxCtrl.sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)

    self.ctrlAxis=ctrlAxis
    pan.SetSizer(sizer)
    pan.Layout()
    self.Centre()
        #self.grid.SetTable(())        


if __name__ == '__main__':
  class App(wx.App):
    def OnInit(self):
      fnHDF='/home/zamofing_t/Documents/prj/libDetXR/python/libDetXR/e14472_00033.hdf5'
      lbl='mcs'
      lbl='pilatus_1'
      fid = h5py.h5f.open(fnHDF)
      hid = h5py.h5o.open(fid,'/entry/dataScan00033/'+lbl)
      frame = HdfGridFrame(None,lbl,hid)
      frame.Show()
      return True
  StopWatch.Start()
  app = App()
  app.MainLoop()
