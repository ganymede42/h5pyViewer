
import wx,h5py
import wx.grid
import numpy as N
#http://wxpython-users.1045709.n5.nabble.com/filling-a-wxgrid-td2348720.html


class Knob:
    """
    Knob - simple class with a "setKnob" method.  
    A Knob instance is attached to a Param instance, e.g. param.attach(knob)
    Base class is for documentation purposes.
    """
    def setKnob(self, value):
        pass


class Param:
    """
    The idea of the "Param" class is that some parameter in the GUI may have
    several knobs that both control it and reflect the parameter's state, e.g.
    a slider, text, and dragging can all change the value of the frequency in
    the waveform of this example.  
    The class allows a cleaner way to update/"feedback" to the other knobs when 
    one is being changed.  Also, this class handles min/max constraints for all
    the knobs.
    Idea - knob list - in "set" method, knob object is passed as well
      - the other knobs in the knob list have a "set" method which gets
        called for the others.
    """
    def __init__(self, initialValue=None, minimum=0., maximum=1.):
        self.minimum = minimum
        self.maximum = maximum
        if initialValue != self.constrain(initialValue):
            raise ValueError('illegal initial value')
        self.value = initialValue
        self.knobs = []
        
    def attach(self, knob):
        self.knobs += [knob]
        
    def set(self, value, knob=None):
        self.value = value
        self.value = self.constrain(value)
        for feedbackKnob in self.knobs:
            if feedbackKnob != knob:
                feedbackKnob.setKnob(self.value)
        return self.value

    def constrain(self, value):
        if value <= self.minimum:
            value = self.minimum
        if value >= self.maximum:
            value = self.maximum
        return value


class SliderGroup(Knob):
    def __init__(self, parent, label, param):
        self.sliderLabel = wx.StaticText(parent, label=label)
        self.sliderText = wx.TextCtrl(parent, -1, style=wx.TE_PROCESS_ENTER)
        self.slider = wx.Slider(parent, -1)
        self.slider.SetMax(param.maximum*1000)
        self.setKnob(param.value)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sliderLabel, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=2)
        sizer.Add(self.sliderText, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=2)
        sizer.Add(self.slider, 1, wx.EXPAND)
        self.sizer = sizer

        self.slider.Bind(wx.EVT_SLIDER, self.sliderHandler)
        self.sliderText.Bind(wx.EVT_TEXT_ENTER, self.sliderTextHandler)

        self.param = param
        self.param.attach(self)

    def sliderHandler(self, evt):
        value = evt.GetInt() / 1000.
        self.param.set(value)
        
    def sliderTextHandler(self, evt):
        value = float(self.sliderText.GetValue())
        self.param.set(value)
        
    def setKnob(self, value):
        self.sliderText.SetValue('%g'%value)
        self.slider.SetValue(value*1000)



class TableBase(wx.grid.PyGridTableBase):
    def __init__(self, data):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = data

    def GetNumberRows(self):
        return self.data.shape[0]

    def GetNumberCols(self):
        return self.data.shape[1]

    def GetValue(self, row, col):
        return self.data[row][col]

class Grid(wx.grid.Grid):
    def __init__(self, parent, data):
        wx.grid.Grid.__init__(self, parent, -1)

        table = TableBase(data)
        self.SetTable (table, True)

class HdfGridFrame(wx.Frame):
    def __init__(self, parent,lbl,hid):
        wx.Frame.__init__(self, parent, title='HDFGridView: '+lbl,size=wx.Size(750, 650))

        pan = wx.Panel(self, -1)

        t=type(hid)
        if t==h5py.h5d.DatasetID:
          obj=h5py.Dataset(hid)
        #grid = Grid(pan, N.random.rand(3000,4000))
        grid = Grid(pan, obj.value)

        self.f0= Param(2., minimum=0., maximum=6.)
        self.frequencySliderGroup = SliderGroup(pan, label='Frequency f0:', \
            param=self.f0)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND)
        sizer.Add(self.frequencySliderGroup.sizer, 0, \
            wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)
        pan.SetSizer(sizer)
        pan.Layout()
        self.Centre()


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
