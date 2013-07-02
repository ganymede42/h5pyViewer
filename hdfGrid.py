
import wx,h5py
import wx.grid
import numpy as N
#http://wxpython-users.1045709.n5.nabble.com/filling-a-wxgrid-td2348720.html

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
          self.cbFuncData[0](0,self.cbFuncData[1])
        
    def sliderTextHandler(self, evt):
        value = int(self.sliderText.GetValue())
        self.slider.SetValue(value)
        value = self.slider.Value
        self.sliderText.SetValue(self.txtFmt%value)
        self.value=value
        if self.cbFuncData:
          self.cbFuncData[0](1,self.cbFuncData[1])
        
class TableBase(wx.grid.PyGridTableBase):
    def __init__(self, data):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data
        self.view = data[0,...]

    def GetNumberRows(self):
        return self.view.shape[0]

    def GetNumberCols(self):
        return self.view.shape[1]

    def GetValue(self, row, col):
        return self.view[row,col]

class Grid(wx.grid.Grid):
  def __init__(self, parent, data):
    wx.grid.Grid.__init__(self, parent, -1)

    table = TableBase(data)
    self.SetTable (table, True)
  @staticmethod
  def OnChangeAxVal(idx,args):
    tbl=args.GetTable()
    tbl.view = tbl.data[10,...]
    pass

class HdfGridFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title='HDFGridView: '+lbl,size=wx.Size(750, 650))

    pan = wx.Panel(self, -1)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      obj=h5py.Dataset(hid)
    #grid = Grid(pan, N.random.rand(3000,4000))
    self.grid = Grid(pan, obj.value)      
    
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(self.grid, 1, wx.EXPAND)
    shape=obj.value.shape
    idxRowCol=(1,2)
    ctrlAxis=[]
    for idx in range(len(shape)-2):
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
      lbl='pilatus_2'
      fid = h5py.h5f.open(fnHDF)
      hid = h5py.h5o.open(fid,'/entry/dataScan00033/'+lbl)
      frame = HdfGridFrame(None,lbl,hid)
      frame.Show()
      return True
  
  app = App()
  app.MainLoop()
