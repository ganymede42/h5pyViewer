#!/usr/bin/env python
#*-----------------------------------------------------------------------*
#|                                                                       |
#|  Copyright (c) 2013 by Paul Scherrer Institute (http://www.psi.ch)    |
#|                                                                       |
#|              Author Thierry Zamofing (thierry.zamofing@psi.ch)        |
#*-----------------------------------------------------------------------*
'''
implements an image view to show a colored image of a hdf5 dataset.
'''

if __name__ == '__main__':
  #Used to guarantee to use at least Wx2.8
  import wxversion
  wxversion.ensureMinimal('2.8')
import wx
import matplotlib as mpl
if __name__ == '__main__':
  mpl.use('WXAgg')
  #or mpl.use('WX')
  #matplotlib.get_backend()

import os,h5py
import numpy as np
import utilities as ut
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import pylab as plt #used for the colormaps
try:
  from libDetXR.procMoment import ProcMoment
except ImportError as e:
  print 'ImportError: '+e.message


#from scipy import ndimage as ndi


#or from matplotlib.backends.backend_wx import FigureCanvasWx as FigureCanvas
#The source of the DraggableColorbar is from:
#http://www.ster.kuleuven.be/~pieterd/python/html/plotting/interactive_colorbar.html

#class ShiftedLogNorm(mpl.colors.Normalize):
class ShiftedLogNorm(mpl.colors.LogNorm):
  #copied and modified from LogNorm
    def __call__(self, value, clip=None):
      #print value.shape,self.vmin,self.vmax,self.clip,clip
      if clip is None:
          clip = self.clip
      ofs0=1-self.vmin
      ofs1=1./(np.log(self.vmax+1-self.vmin))
      result=np.log(value+ofs0)*ofs1
      result = np.ma.masked_less_equal(result, 0, copy=False)
      return result
    def inverse(self, value):
        if not self.scaled():
            raise ValueError("Not invertible until scaled")
        vmin, vmax = self.vmin, self.vmax
        ofs0=1-vmin
        if mpl.cbook.iterable(value):
          val = np.ma.asarray(value)
          return vmin * np.ma.power((vmax/vmin), val)-ofs0
        else:
          return vmin * pow((vmax/vmin), value)-ofs0
    def autoscale_None(self, A):
      if self.vmin is None:
          self.vmin = np.ma.min(A)
      if self.vmax is None:
          self.vmax = np.ma.max(A)
      pass
    def autoscale(self, A):
      pass

class MPLCanvasImg(FigureCanvas):
  def __init__(self,parent,SetStatusCB=None):
    if SetStatusCB:
      self.SetStatusCB=SetStatusCB
    fig = mpl.figure.Figure()
    ax = fig.add_axes([0.075,0.1,0.75,0.85])
    FigureCanvas.__init__(self,parent, -1, fig)
    self.mpl_connect('motion_notify_event', self.OnMotion)
    self.mpl_connect('button_press_event',   self.OnBtnPress)
    self.mpl_connect('button_release_event', self.OnBtnRelease)
    self.mpl_connect('scroll_event', self.OnBtnScroll)
    self.mpl_connect('key_press_event',self.OnKeyPress)
    self.fig=fig
    self.ax=ax

  def InitChild(self,data):
    if data.dtype==np.complex128:
      self.dataRaw=data
      #data=np.angle(data)
      data=np.absolute(data)

    fig=self.fig
    ax=self.ax

    msk=~np.isnan(data);msk=data[msk]
    avg=np.average(msk); std=np.std(msk)
    vmin=np.min(msk);vmax=np.max(msk)
    vmin=max(vmin,avg-3*std);vmax=min(vmax,avg+3*std)
    if vmin==0:vmin=1
    if vmax<=vmin:
      vmax=vmin+1

    #norm=ShiftedLogNorm()
    norm=mpl.colors.Normalize()
    #img = ax.imshow(data,interpolation='nearest',cmap=mpl.cm.jet, norm=ShiftedLogNorm(vmin=vmin, vmax=vmax))

    img = ax.imshow(data,interpolation='nearest',cmap=mpl.cm.jet, vmin=vmin, vmax=vmax)
    colBar=fig.colorbar(img,orientation='vertical',norm=norm)
    #colBar.norm=ShiftedLogNorm(vmin=vmin, vmax=vmax)
    colBar.norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    img.set_norm(colBar.norm)
    img.cmap._init();bg=img.cmap._lut[0].copy();bg[:-1]/=4
    ax.set_axis_bgcolor(bg)


    self.colBar=colBar
    self.colCycle = sorted([i for i in dir(plt.cm) if hasattr(getattr(plt.cm,i),'N')])
    self.colIndex = self.colCycle.index(colBar.get_cmap().name)
    self.img=img

  def OnMotion(self,event):
    #print event,event.x,event.y,event.inaxes,event.xdata,event.ydata
    if event.inaxes==self.ax:
      x=int(round(event.xdata))
      y=int(round(event.ydata))
      try:
        v=self.img.get_array()[y,x]
      except IndexError as e:
        pass
      else:
        #print x,y,v
        self.SetStatusCB(self.Parent,0,(x,y,v))
    elif event.inaxes==self.colBar.ax:
      colBar=self.colBar
      pt=colBar.ax.bbox.get_points()[:,1]
      nrm=colBar.norm
      vmin,vmax,p0,p1,pS = (nrm.vmin,nrm.vmax,pt[0],pt[1],event.y)
      if isinstance(colBar.norm,mpl.colors.LogNorm):#type(colBar.norm)==mpl.colors.LogNorm does not work...
        vS=0
      else:#scale around point
        vS=vmin+(vmax-vmin)/(p1-p0)*(pS-p0)
      self.SetStatusCB(self.Parent,1,vS)
    try:
      vmin,vmax,p0,p1,pS=self.colBarPressed
    except AttributeError:
      return
      #if event.inaxes != self.cbar.ax: return
    colBar=self.colBar
    #print vmin,vmax,p0,p1,pS,type(colBar.norm)
    #print 'x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f'%(x0, xpress, event.xdata, dx, x0+dx)

    if isinstance(colBar.norm,mpl.colors.LogNorm):#type(colBar.norm)==mpl.colors.LogNorm does not work...
      if event.button==1:
        #colBar.norm.vmin=.1
        colBar.norm.vmax=vmax*np.exp((pS-event.y)/100)
        #scale= np.exp((event.y-pS)/100)
    elif event.button==1:#move top,bottom,both
      pD = event.y - pS
      vD=(vmax-vmin)/(p1-p0)*(pS-event.y)
      colBar.norm.vmin = vmin+vD
      colBar.norm.vmax = vmax+vD
    elif event.button==3:#scale around point
      scale= np.exp((pS-event.y)/100)
      vS=vmin+(vmax-vmin)/(p1-p0)*(pS-p0)
      #print scale,vS
      colBar.norm.vmin = vS-scale*(vS-vmin)
      colBar.norm.vmax = vS-scale*(vS-vmax)
    self.img.set_norm(colBar.norm)#force image to redraw
    colBar.patch.figure.canvas.draw()

  def OnBtnPress(self, event):
    """on button press we will see if the mouse is over us and store some data"""
    #print dir(event.guiEvent)
    if event.inaxes == self.colBar.ax:
      #if event.guiEvent.LeftDClick()==True:
      #    print dlg
      pt=self.colBar.ax.bbox.get_points()[:,1]
      nrm=self.colBar.norm
      self.colBarPressed = (nrm.vmin,nrm.vmax,pt[0],pt[1],event.y)
      #self.colBarPressed = event.x, event.y
      #print self.colBarPressed
      #self.OnMouse(event)
    pass

  def OnBtnRelease(self, event):
    """on release we reset the press data"""
    #self.OnMouse(event)
    try: del self.colBarPressed
    except AttributeError: pass

  def OnBtnScroll(self, event):
    #self.OnMouse(event)
    colBar=self.colBar
    if event.inaxes==colBar.ax:
      pt=colBar.ax.bbox.get_points()[:,1]
      nrm=colBar.norm
      vmin,vmax,p0,p1,pS = (nrm.vmin,nrm.vmax,pt[0],pt[1],event.y)
      if isinstance(colBar.norm,mpl.colors.LogNorm):#type(colBar.norm)==mpl.colors.LogNorm does not work...
        scale= np.exp((-event.step)/10)
        colBar.norm.vmax=vmax*scale
      else:#scale around point
        scale= np.exp((-event.step)/10)
        vS=vmin+(vmax-vmin)/(p1-p0)*(pS-p0)
        #print scale,vS
        colBar.norm.vmin = vS-scale*(vS-vmin)
        colBar.norm.vmax = vS-scale*(vS-vmax)
      self.img.set_norm(colBar.norm)#force image to redraw
      colBar.patch.figure.canvas.draw()

  def OnKeyPress(self, event):
    colCycle=self.colCycle
    colBar=self.colBar
    if event.key=='down':
      self.colIndex += 1
    elif event.key=='up':
      self.colIndex -= 1
    self.colIndex%=len(colCycle)
    cmap = colCycle[self.colIndex]
    colBar.set_cmap(cmap)
    colBar.draw_all()
    self.img.set_cmap(cmap)
    self.img.get_axes().set_title(cmap)
    colBar.patch.figure.canvas.draw()

  def OnMouse(self, event):
    for k in dir(event):
      if k[0]!='_':
        print k,getattr(event,k)

class DlgColBarSetupOld(wx.Dialog):
  def __init__(self,parent):
    wx.Dialog.__init__(self,parent,-1,'Colormap Setup')
    colBar=parent.canvas.colBar
    cmap=colBar.cmap
    nrm=colBar.norm
    txtVMin=wx.StaticText(self,-1,'vmin')
    txtVMax=wx.StaticText(self,-1,'vmax')
    self.edVMin=edVMin=wx.TextCtrl(self,-1,'%g'%nrm.vmin)
    self.edVMax=edVMax=wx.TextCtrl(self,-1,'%g'%nrm.vmax)
    sizer=wx.BoxSizer(wx.VERTICAL)
    fgs=wx.FlexGridSizer(3,2,5,5)
    fgs.Add(txtVMin,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMin,0,wx.EXPAND)
    fgs.Add(txtVMax,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMax,0,wx.EXPAND)
    sizer.Add(fgs,0,wx.EXPAND|wx.ALL,5)

    edVMin.SetFocus()

    btns =  self.CreateButtonSizer(wx.OK|wx.CANCEL)
    sizer.Add(btns,0,wx.EXPAND|wx.ALL,5)
    self.Bind(wx.EVT_BUTTON, self.OnBtnOk, id=wx.ID_OK)

    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnBtnOk(self, event):
    event.Skip()#do not consume (use event to close the window and sent return code)
    print 'OnBtnOk'
    parent=self.GetParent()
    canvas=parent.canvas
    colBar=canvas.colBar
    colBar.norm.vmin=float(self.edVMin.Value)
    colBar.norm.vmax=float(self.edVMax.Value)
    canvas.img.set_norm(colBar.norm)
    #colBar.patch.figure.canvas.draw()
    canvas.draw()


class DlgColBarSetup(wx.Dialog):
  def __init__(self,parent):
    wx.Dialog.__init__(self,parent,-1,'Colormap Setup')
    colBar=parent.canvas.colBar
    cmap=colBar.cmap
    nrm=colBar.norm

    txtVMin=wx.StaticText(self,-1,'vmin')
    txtVMax=wx.StaticText(self,-1,'vmax')
    txtColMap=wx.StaticText(self,-1,'colormap')
    self.edVMin=edVMin=wx.TextCtrl(self,-1,'%g'%nrm.vmin,style=wx.TE_PROCESS_ENTER)
    self.edVMax=edVMax=wx.TextCtrl(self,-1,'%g'%nrm.vmax,style=wx.TE_PROCESS_ENTER)

    txtTxrFunc=wx.StaticText(self,-1,'function')
    self.cbtxrFunc=cbtxrFunc=wx.ComboBox(self, -1, choices=('linear','logarithmic'), style=wx.CB_READONLY)
    cbtxrFunc.SetSelection(0 if nrm.__class__==mpl.colors.Normalize else 1)

    #colMapLst=('Accent', 'Blues', 'BrBG', 'BuGn', 'BuPu', 'Dark2', 'GnBu', 'Greens', 'Greys', 'OrRd', 'Oranges', 'PRGn', 'Paired',
    #'Pastel1', 'Pastel2', 'PiYG', 'PuBu', 'PuBuGn', 'PuOr', 'PuRd', 'Purples', 'RdBu', 'RdGy', 'RdPu', 'RdYlBu', 'RdYlGn', 'Reds',
    #'Set1', 'Set2', 'Set3', 'Spectral', 'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd', 'afmhot', 'autumn', 'binary', 'bone', 'brg', 'bwr',
    #'cool', 'coolwarm', 'copper', 'cubehelix', 'flag', 'gist_earth', 'gist_gray', 'gist_heat', 'gist_ncar', 'gist_rainbow', 'gist_stern',
    #'gist_yarg', 'gnuplot', 'gnuplot2', 'gray', 'hot', 'hsv', 'jet', 'ocean', 'pink', 'prism', 'rainbow', 'seismic', 'spectral',
    #'spring', 'summer', 'terrain', 'winter')

    colMapLst=('hot','spectral','jet','gray','RdYlBu','hsv','gist_stern','gist_ncar','BrBG','RdYlBu','brg','gnuplot2',
               'prism','rainbow',)

    self.cbColMap=cbColMap=wx.ComboBox(self, -1, choices=colMapLst, style=wx.CB_READONLY)
    cbColMap.Value=cmap.name

    sizer=wx.BoxSizer(wx.VERTICAL)
    fgs=wx.FlexGridSizer(4,2,5,5)
    fgs.Add(txtVMin,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMin,0,wx.EXPAND)
    fgs.Add(txtVMax,0,wx.ALIGN_RIGHT)
    fgs.Add(edVMax,0,wx.EXPAND)
    fgs.Add(txtTxrFunc,0,wx.ALIGN_RIGHT)
    fgs.Add(cbtxrFunc,0,wx.EXPAND)
    fgs.Add(txtColMap,0,wx.ALIGN_RIGHT)
    fgs.Add(cbColMap,0,wx.EXPAND)
    sizer.Add(fgs,0,wx.EXPAND|wx.ALL,5)

    edVMin.SetFocus()

    btns =  self.CreateButtonSizer(wx.OK|wx.CANCEL)
    btnApply=wx.Button(self, -1, 'Apply')
    btns.Add(btnApply, 0, wx.ALL, 5)
    sizer.Add(btns,0,wx.EXPAND|wx.ALL,5)
    self.Bind(wx.EVT_BUTTON, self.OnModify, id=wx.ID_OK)
    self.Bind(wx.EVT_BUTTON, self.OnModify, btnApply)
    #self.Bind(wx.EVT_TEXT_ENTER, self.OnModify, edVMin)
    #self.Bind(wx.EVT_TEXT_ENTER, self.OnModify, edVMax)
    self.Bind(wx.EVT_TEXT, self.OnModify, edVMin)
    self.Bind(wx.EVT_TEXT, self.OnModify, edVMax)
    self.Bind(wx.EVT_COMBOBOX, self.OnModify, cbtxrFunc)
    self.Bind(wx.EVT_COMBOBOX, self.OnModify, cbColMap)

    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnModify(self, event):
    #print 'OnModify'
    parent=self.GetParent()
    canvas=parent.canvas
    colBar=canvas.colBar
    cmap=colBar.cmap
    nrm=colBar.norm
    img=canvas.img
    ax=img.get_axes()
    data=img.get_array()

    v=self.cbColMap.Value
    if v!=cmap.name:
      cmap=getattr(mpl.cm,v)
      colBar.set_cmap(cmap)
      colBar.draw_all()
      img.set_cmap(cmap)
      ax.set_title(cmap.name)
      colBar.patch.figure.canvas.draw()

    vmin,vmax=(float(self.edVMin.Value),float(self.edVMax.Value))
    nrm.vmin=vmin; nrm.vmax=vmax
    v=self.cbtxrFunc.GetCurrentSelection()
    func=(mpl.colors.Normalize,ShiftedLogNorm)
    if nrm.__class__!=func[v]:
      if v==0: #linear mapping
        colBar.norm = mpl.colors.Normalize(vmin, vmax)
      elif v==1: #log mapping
        img.cmap._init();bg=img.cmap._lut[0].copy();bg[:-1]/=4
        ax.set_axis_bgcolor(bg)
        vmin=1
        colBar.norm = mpl.colors.LogNorm(vmin,vmax)
    img.set_norm(colBar.norm)
    colBar.patch.figure.canvas.draw()
    parent.Refresh(False)
    if event.GetId()==wx.ID_OK:
      event.Skip()#do not consume (use event to close the window and sent return code)

class HdfImageFrame(wx.Frame):
  def __init__(self, parent,lbl,hid):
    wx.Frame.__init__(self, parent, title=lbl, size=wx.Size(850, 650))
    imgDir=ut.Path.GetImage()
    icon = wx.Icon(os.path.join(imgDir,'h5pyViewer.ico'), wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    t=type(hid)
    if t==h5py.h5d.DatasetID:
      data=h5py.Dataset(hid)

    canvas =  MPLCanvasImg(self,self.SetStatusCB)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
    self.SetSizer(sizer)

    toolbar=ut.AddToolbar(canvas,sizer)

    wxAxCtrlLst=[]
    l=len(data.shape)
    idxXY=(l-2,l-1)
    for idx,l in enumerate(data.shape):
      if idx in idxXY:
        continue
      wxAxCtrl=ut.SliderGroup(self, label='Axis:%d'%idx,range=(0,l-1))
      wxAxCtrl.idx=idx
      wxAxCtrlLst.append(wxAxCtrl)
      sizer.Add(wxAxCtrl.sizer, 0, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border=5)
      wxAxCtrl.SetCallback(HdfImageFrame.OnSetView,wxAxCtrl)

    sl=ut.GetSlice(idxXY,data.shape,wxAxCtrlLst)

    canvas.InitChild(data[sl])

    #self.Fit()
    self.Centre()

    self.BuildMenu(data.dtype)
    self.canvas=canvas
    self.sizer=sizer
    self.toolbar=toolbar
    self.data=data
    self.idxXY=idxXY
    self.wxAxCtrlLst=wxAxCtrlLst

  def BuildMenu(self,dtype):
    mnBar = wx.MenuBar()

    #-------- Edit Menu --------
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Setup Colormap', 'Setup the color mapping ');self.Bind(wx.EVT_MENU, self.OnColmapSetup, mnItem)
    mnItem=mn.Append(wx.ID_ANY, 'Invert X-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    self.mnIDxAxis=mnItem.GetId()
    mnItem=mn.Append(wx.ID_ANY, 'Invert Y-Axis', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnInvertAxis, mnItem)
    mnItem=mn.Append(wx.ID_ANY, 'Show Moments', 'Show image moments ', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnShowMoments, mnItem)
    self.mnItemShowMoment=mnItem
    mnItem=mn.Append(wx.ID_ANY, 'Tomo Normalize', 'Multiplies each pixel with a normalization factor. Assumes there exist an array exchange/data_white', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnTomoNormalize, mnItem)
    self.mnItemTomoNormalize=mnItem

    if dtype==np.complex128:
      mnItem=mn.Append(wx.ID_ANY, 'Complex: Phase', kind=wx.ITEM_CHECK);self.Bind(wx.EVT_MENU, self.OnSetComplexData, mnItem)


    mnBar.Append(mn, '&Edit')
    mn = wx.Menu()
    mnItem=mn.Append(wx.ID_ANY, 'Help', 'How to use the image viewer');self.Bind(wx.EVT_MENU, self.OnHelp, mnItem)
    mnBar.Append(mn, '&Help')

    self.SetMenuBar(mnBar)
    self.CreateStatusBar()

  def SetIdxXY(self,x,y):
    self.idxXY=(x,y)

  @staticmethod
  def SetStatusCB(obj,mode,v):
    if mode==0:
      obj.SetStatusText( "x= %d y=%d val=%g"%v,0)
    elif mode==1:
      obj.SetStatusText( "Colormap Value %d (drag to scale)"%v,0)
    else:
      raise KeyError('wrong mode')

  @staticmethod
  def OnSetView(usrData,value,msg):
    'called when a slice is selected with the slider controls'
    imgFrm=usrData.slider.Parent
    #imgFrm.img.set_array(imgFrm.data[usrData.value,...])
    data=imgFrm.data
    sl=ut.GetSlice(imgFrm.idxXY,data.shape,imgFrm.wxAxCtrlLst)

    try:
      tomoNorm=imgFrm.tomoNorm
    except AttributeError:
      imgFrm.canvas.img.set_array(data[sl])
    else:
      data=data[sl]*tomoNorm
      imgFrm.canvas.img.set_array(data)

    if imgFrm.mnItemShowMoment.IsChecked():
      imgFrm.PlotMoments()
    imgFrm.canvas.draw()
    pass

  def OnShowMoments(self,event):
    if event.IsChecked():
      dlg = wx.FileDialog(self, "Choose valid mask file (e.g. pilatus_valid_mask.mat)", os.getcwd(), '','MATLAB files (*.mat)|*.mat|all (*.*)|*.*', wx.OPEN|wx.FD_CHANGE_DIR)
      if dlg.ShowModal() == wx.ID_OK:
        fnMatMsk = dlg.GetPath()
        print 'OnOpen',fnMatMsk
      dlg.Destroy()
      if not fnMatMsk:
        return
      #fnMatMsk='/scratch/detectorData/cSAXS_2013_10_e14608_georgiadis_3D_for_Marianne/analysis/data/pilatus_valid_mask.mat'
      self.procMoment=pm=ProcMoment()
      pm.SetMskMat(fnMatMsk,False)
      #roi=[603, 826, 200, 200]
      #pm.roi=(slice(roi[1],roi[1]+roi[3]),slice(roi[0],roi[0]+roi[2]))
      #pm.shape=(roi[3],roi[2])

      #pm.SetProcess('python')
      #pm.SetProcess('pyFast')
      pm.SetProcess('c')
      self.PlotMoments()
      #self.canvas.img.draw()
      data=self.canvas.img.get_array()
      self.canvas.img.set_array(data)
      fig, ax = plt.subplots(2)
      v=data.sum(axis=0); x=np.arange(v.size); x0=x.sum(); m0=v.sum(); m1=(v*x).sum(); m2=(v*x*x).sum()
      ax[0].plot(v);
      m=m1/m0
      s=np.sqrt( (m2-(m1**2/m0))/m0)
      xx=1/(s*np.sqrt(2*np.pi))*np.exp(-.5*((x-m)/s)**2)
      ax[0].set_title('%g | %g | %g | %g | %g'%(m0,m1,m2,m,s))
      ax[0].hold(True);ax[0].plot(xx*m0)

      v=data.sum(axis=1);
      ax[1].plot(v);


      plt.show()
      #print pm.resArr[0:3],pm.resArr[1]/pm.resArr[0],pm.resArr[2]/pm.resArr[0]
    else:
      for o in self.goMoment:
        o.remove()
      del self.goMoment
      del self.procMoment
    self.canvas.draw()

  def PlotMoments(self):
    data=self.canvas.img.get_array()
    pm=self.procMoment

    #data=ndi.median_filter(data, 3)
    try:
      data.ravel()[pm.mskIdx]=0
    except AttributeError as e:
      print e
    try:
      data=data[pm.roi]
    except AttributeError as e:
      print e
    #data=np.log(data+1)
    #data[100:110,500:510]=1000 #y,x
    #data[650:850,700:850]=0 #y,x
    #pm.Process(np.log(data+1))
    pm.Process(data)
    xbar, ybar, cov=pm.GetIntertialAxis()

    m=pm.resArr
    m00=m[0];m01=m[1];m10=m[2];m11=m[3];m02=m[4];m20=m[5]

    xm = m10 / m00
    ym = m01 / m00
    u11 = (m11 - xm * m01) / m00
    #u11[u11<0.]=0. #processing rounding error
    u20 = (m20 - xm * m10) / m00
    u02 = (m02 - ym * m01) / m00
    a=(u20+u02)/2
    b=np.sqrt(4*u11**2+(u20-u02)**2)/2
    l0=a+b
    l1=a-b
    ang=0.5*np.arctan2(2*u11,(u20-u02))/(2*np.pi)*360. #orientation value 0..1
    exc=np.sqrt(1-l1/l0) #eccentricity :circle=0: http://en.wikipedia.org/wiki/Eccentricity_%28mathematics%29

    print 'xb:%g yb:%g cov:%g %g %g %g  ang:%g exc:%g'%((xm, ym)+tuple(cov.ravel())+(ang,exc))
    #fig, ax = plt.subplots()
    #ax.imshow(data,vmax=100,interpolation='nearest')
    #plt.show()
    ax=self.canvas.img.get_axes()
    try:
      for o in self.goMoment:
        o.remove()
    except AttributeError: pass

    self.goMoment=ProcMoment.PlotMoments(ax, xbar, ybar, cov)
    ax.axis('image')

  def OnTomoNormalize(self,event):
    if event.IsChecked():
      #try to find white image
      #calculate average
      #show white normalize factors
      white=self.data.parent['data_white']
      tomoNorm=white[1,:,:]
      #tomoNorm=white[:,:,:].mean(axis=0)
      #np.iinfo(tomoNorm.dtype).max
      #tomoNorm=float(np.iinfo(tomoNorm.dtype).max/2)/tomoNorm
      tomoNorm=tomoNorm.mean()/tomoNorm
      #tomoNorm=tomoNorm/float(np.iinfo(tomoNorm.dtype).max)
      data=self.canvas.img.get_array()
      data*=tomoNorm
      #data/=tomoNorm
      self.tomoNorm=tomoNorm
      self.canvas.img.set_array(data)
    else:
      tomoNorm=self.tomoNorm
      data=self.canvas.img.get_array()
      data/=tomoNorm
      self.canvas.img.set_array(data)
      del self.tomoNorm
    self.canvas.draw()

  def OnSetComplexData(self, event):
    if event.IsChecked():
      data=np.angle(self.canvas.dataRaw)
    else:
      data=np.absolute(self.canvas.dataRaw)
    self.canvas.img.set_array(data)
    self.canvas.draw()

  def OnHelp(self,event):
    msg='''to change the image selection:
use the toolbar at the bottom to pan and zoom the image
use the scrollbars at the bottom (if present) to select an other slice

to change the colorscale:
drag with left mouse button to move the colorbar up and down
drag with right mouse button to zoom in/out the colorbar at a given point
use mouse weel to zoom in/out the colorbar at a given point
double click left mouse button to set maximum and minimun colorbar values
use cursor up and down to use a different colormap'''
    dlg = wx.MessageDialog(self, msg, 'Help', wx.OK|wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

  def OnColmapSetup(self,event):
    dlg=DlgColBarSetup(self)
    if dlg.ShowModal()==wx.ID_OK:
      pass
    dlg.Destroy()

  def OnInvertAxis(self,event):
    ax=self.canvas.ax
    #event.Checked()
    if self.mnIDxAxis==event.GetId():
      ax.invert_xaxis()
    else:
      ax.invert_yaxis()
    self.canvas.draw()
    pass

if __name__ == '__main__':
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):
    fnHDF='/scratch/detectorData/e14472_00033.hdf5'
    #lbl='mcs'
    lbl='pilatus_1'
    #lbl='spec'
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
      frame = HdfImageFrame(None,args.elem,hid)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()
