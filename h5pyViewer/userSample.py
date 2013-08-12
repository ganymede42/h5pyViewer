#this is a sample user module to test lolading modules from the  h5pyViewer python shell
#in python shell of h5pyViewer call:
#import userSample as us;reload(us);us.test1(hid)
import h5py
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

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

