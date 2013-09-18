if __name__ == '__main__':
  #Used to guarantee to use at least Wx2.8
  import wxversion
  wxversion.ensureMinimal('2.8')
import wx
import matplotlib as mpl
if __name__ == '__main__':
  mpl.use('WXAgg') #or mpl.use('WX')

from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import time,os

class Path():
  @staticmethod
  def GetImage():
    path=__file__
    try:symPath=os.readlink(path) #follow symbolic link
    except (AttributeError,OSError) as e:pass
    else:
      path=symPath
    path=os.path.abspath(path)
    path=os.path.dirname(path)
    return os.path.join(path,'images')

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
  def __init__(self, parent, label, range=(0,100),val=0):
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
    self.SetValue(val)

  def SetValue(self, value):
    self.value = value
    self.slider.SetValue(value)
    self.sliderText.SetValue(str(value))
  
  def SetCallback(self,funcCB,usrData):
    self.cbFuncData=(funcCB,usrData)

  def Callback(self,value,msg):
    try:
      (funcCB,usrData)=self.cbFuncData
    except BaseException as e:
      pass
    else:
      funcCB(usrData,value,msg)

  def sliderHandler(self, evt):
    value = evt.GetInt()
    self.sliderText.SetValue(str(value))
    self.value=value
    self.Callback(value,0)      
      
  def sliderTextHandler(self, evt):
    value = int(self.sliderText.GetValue())
    self.slider.SetValue(value)
    value = self.slider.Value
    self.sliderText.SetValue(str(value))
    self.value=value
    self.Callback(value,0)      

def GetSlice(idxXY,shp,wxAxCtrlLst):
  '''returns a slice list to select data'''
  sl=[None]*len(shp)
  for ax in wxAxCtrlLst:
    sl[ax.idx]=ax.value
  for i in idxXY:
    sl[i]=slice(None)
  sl=tuple(sl)
  return sl


def AddToolbar(parent,sizer):
  toolbar = NavigationToolbar(parent)
  toolbar.Realize()
  if wx.Platform == '__WXMAC__':
    # Mac platform (OSX 10.3, MacPython) does not seem to cope with
    # having a toolbar in a sizer. This work-around gets the buttons
    # back, but at the expense of having the toolbar at the top
    parent.SetToolBar(toolbar)
  else:
    # On Windows platform, default window size is incorrect, so set
    # toolbar width to figure width.
    tw, th = toolbar.GetSizeTuple()
    fw, fh = parent.GetSizeTuple()
    # By adding toolbar in sizer, we are able to put it at the bottom
    # of the frame - so appearance is closer to GTK version.
    # As noted above, doesn't work for Mac.
    toolbar.SetSize(wx.Size(fw, th))
    sizer.Add(toolbar, 0, wx.LEFT | wx.EXPAND)
  # update the axes menu on the toolbar
  toolbar.update()
  return toolbar

