#this is a sample user module to test lolading modules from the  h5pyViewer python shell
#in python shell of h5pyViewer call:
#import userSample as us;reload(us);us.test1(hid)
import h5py
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot1d(hid):
  print hid
  ds=h5py.Dataset(hid)
  ds
  plt.plot(ds[0,:])
  plt.show()

def test1(hid):
  print hid
  ds=h5py.Dataset(hid)
  ds
  plt.plot(ds[:,1])
  plt.show()

def test2(hid):
  ds=h5py.Dataset(hid)
  ds
  plt.plot(ds[:,0])
  plt.show()

def GetAttrVal(aid):
  rtdt = h5py._hl.dataset.readtime_dtype(aid.dtype, []) 
  arr = np.ndarray(aid.shape, dtype=rtdt, order='C')
  aid.read(arr)
  if len(arr.shape) == 0:
    return arr[()]
  return arr

def test3(hid):
    numAttr=h5py.h5a.get_num_attrs(hid)
    for idxAttr in range(numAttr):
      aid=h5py.h5a.open(hid,index=idxAttr)
      val=GetAttrVal(aid)
      print aid.name,val
      if aid.name=='ofsTime':
        plt.plot(val)
        plt.show()

