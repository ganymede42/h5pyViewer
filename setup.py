#! /usr/bin/env python

#FOR DISTUTILS READ:
#http://docs.python.org/2/distutils/index.html

import distutils.core, distutils.dist
import distutils.command.sdist, distutils.command.build_py,distutils.command.install_lib
import re

import sys,os,platform,subprocess
#python setup.py --help-commands
#python setup.py --help

#python setup.py --name --version --fullname --author --author-email  --maintainer  --maintainer-email --contact --contact-email  --url  --license  --description --long-description --platforms --classifiers --keywords --provides --requires --obsoletes

#python setup.py build
#python setup.py build

#python setup.py install --prefix=~/ 
#python setup.py bdist_egg

#python setup.py install --root tmp
#python setup.py bdist --formats=wininst
#python setup.py bdist_wininst
#python setup.py bdist

#Command Line : --help-commands
#Standard commands:
#  build            build everything needed to install
#  build_py         "build" pure Python modules (copy to build directory)
#  build_ext        build C/C++ extensions (compile/link to build directory)
#  build_clib       build C/C++ libraries used by Python extensions
#  build_scripts    "build" scripts (copy and fixup #! line)
#  clean            clean up temporary files from 'build' command
#  install          install everything from build directory
#  install_lib      install all Python modules (extensions and pure Python)
#  install_headers  install C/C++ header files
#  install_scripts  install scripts (Python or otherwise)
#  install_data     install data files
#  sdist            create a source distribution (tarball, zip file, etc.)
#  register         register the distribution with the Python package index
#  bdist            create a built (binary) distribution
#  bdist_dumb       create a "dumb" built distribution
#  bdist_rpm        create an RPM distribution
#  bdist_wininst    create an executable installer for MS Windows
#  upload           upload binary package to PyPI
#  check            perform some checks on the package

def getVersion():
  #for dirname, dirnames, filenames in os.walk('.'):
  #  for subdirname in dirnames:
  #    print os.path.join(dirname, subdirname)
  #  for filename in filenames:
  #    print os.path.join(dirname, filename)

  fn='./PKG-INFO'
  if os.access(fn, os.R_OK):
    sys.stdout.write('getVersion() -> Parsing '+fn)
    fo=open(fn,'r')
    for ln in fo.readlines():
      if ln.startswith('Version:'):
        ver=re.match('Version:\s*(\S*)', ln).group(1)
      elif ln.startswith('Summary:'):
        #print ln
        gitcmt=re.search('\(git:(.*)\)', ln).group(1)
    fo.close()
  else:
    argv=sys.argv
    p = subprocess.Popen('git rev-list HEAD', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #p = subprocess.Popen('git log --pretty=%h', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = p.wait()
    res=p.stdout.readlines()
    ver=len(res)
    ver='0.0.0.'+str(ver)
    gitcmt=res[0][:7]
    sys.stdout.write('getVersion() -> using git command')
  print ':'+ver+':'+gitcmt
  return (ver,gitcmt)

def runSetup(**kv):
  ver=getVersion()

  args={#'cmdclass'    :{'sdist': MySDIST, 'build_py': MyBUILD_PY, 'install_lib':MyINSTALL_LIB},
        'name'        :'h5pyViewer',
        'version'     : ver[0],
        'description' :'(git:'+ver[1]+') HDF5-File-Viewer',
        'author'      :'Thierry Zamofing',
        'author_email':'thierry.zamofing@psi.ch',
        'maintainer'  :'Thierry Zamofing',
        'maintainer_email':'thierry.zamofing@psi.ch',
        'url'         :'www.psi.ch',
        'license'     :'(c) 2013 PSI',
        'long_description':open('README.rst', 'r').read(),
        'platforms'   : ['Linux','Windows'],
        #'py_modules'  :['libDetXR', 'cbfParser'],
        'packages'    :['h5pyViewer'],
        #'package_dir' :{'h5pyViewer':'.'},
        'package_data':{'h5pyViewer': ['images/*.png','images/*.ico']},
        #'requires' requires: h5py==2.0.1 libDetXR==0.0.0.6 numpy==1.7.1 matplotlib==1.2.0 
        'requires' : ['ctypes','h5py','numpy','matplotlib']
      }
  if kv:
    args.update(kv)
  distutils.core.setup(**args)

  print 'done'
  pass

def main():
  argv=sys.argv
  if 'debug' in argv:
    script_args=['--name', '--version', '--fullname', '--author', '--author-email', '--maintainer', '--maintainer-email', '--contact', '--contact-email', '--url', '--license', '--description', '--long-description', '--platforms', '--classifiers', '--keywords', '--provides', '--requires', '--obsoletes']
    runSetup(script_args=script_args)
  else:
    runSetup()
  pass

if __name__ == '__main__':
    main()

