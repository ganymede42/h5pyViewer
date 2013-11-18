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
import os,h5py
from GLCanvasImg import *
from libDetXR.procRoiStat import ProcRoiStat

from hdfImageGL import HdfImageGLFrame
from glumpy.image.texture import Texture
from scipy import ndimage as ndi

###########################################

class ProcRoiStatFrame(HdfImageGLFrame):
  def __init__(self, parent, title, hid,fnMatRoi):
    HdfImageGLFrame.__init__(self, parent, title, hid)
    #HdfPyFAI1DFrame(self, title, hid)
    canvas=self.canvas
    raw=canvas.data
    
    self.prs=prs=ProcRoiStat()
    prs.SetRoiMat(fnMatRoi,raw.shape)
    prs.SetProcess('avg')
    print 'numnber of ROI,',prs.roiLenArr.size,'Total number of pixels',prs.roiIdxArr.size
    prs.Process_C(raw)
    print prs.resArr[0,:].max(),prs.resArr[0,:].min()
    canvas.data=np.rot90(prs.resArr[0,:].reshape(-1,prs.mskNumSeg))

  def BuildMenu(self):
    HdfImageGLFrame.BuildMenu(self)
    mnBar=self.GetMenuBar()
    mn=mnBar.GetMenu(0)
    itemLst=mn.GetMenuItems()
    it=itemLst[0]
    it.GetItemLabel()
    #mnItem=mn.Append(wx.ID_ANY, 'Setup FAI', 'Setup fast azimutal integration ');self.Bind(wx.EVT_MENU, self.OnFAISetup, mnItem)

  @staticmethod
  def OnSetView(usrData,value,msg):
    'called when a slice is selected with the slider controls'
    frm=usrData.slider.Parent
    ds=frm.dataSet
    canvas=frm.canvas
    glImg=canvas.glImg
    sl=ut.GetSlice(frm.idxXY,ds.shape,frm.wxAxCtrlLst)
    
    prs=frm.prs
    prs.Process_C(ds[sl])
    canvas.data[:]=(np.rot90(prs.resArr[0,:].reshape(-1,prs.mskNumSeg)))[:]
    glImg.data[:]=canvas.GetTxrData()
    glImg.update()
    canvas.OnPaint(None)#force to repaint, Refresh and Update do not force !
    #canvas.Refresh(False)
    #canvas.Update()
    pass

  def OnProcRoiStatSetup(self, event):
    dlg=DlgSetupProcRoiStat(self)
    if dlg.ShowModal()==wx.ID_OK:
      pass
    dlg.Destroy()


  
if __name__ == '__main__':
  import os,sys,argparse #since python 2.7
  def GetParser(required=True):
    fnHDF='/scratch/detectorData/cSAXS_2013_10_e14608_georgiadis_3D_for_Marianne/scan_00106-00161.hdf5'
    lbl='pilatus_1'
    elem='/entry/data/'+lbl
    fnMatRoi='/scratch/detectorData/cSAXS_2013_10_e14608_georgiadis_3D_for_Marianne/analysis/data/pilatus_integration_mask.mat'    
    exampleCmd='--hdfFile='+fnHDF+' --elem='+elem
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__,
                                     epilog='Example:\n'+os.path.basename(sys.argv[0])+' '+exampleCmd+'\n ')
    parser.add_argument('--matRoi', required=required, default=fnMatRoi, help='the hdf5 to show')
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
      frame = ProcRoiStatFrame(None,args.elem,hid,args.matRoi)
      frame.Show()
      self.SetTopWindow(frame)
      return True

    def OnExit(self):
      self.fid.close()

  ut.StopWatch.Start()
  app = App()
  app.MainLoop()


