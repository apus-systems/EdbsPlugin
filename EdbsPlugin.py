"""
/***************************************************************************
  Name         : EDBS plugin
  Description  : conversion of EDBS data to polygon, line and point layers
  Date         : 2013-06-30 
  Copyright    : (c) 2013, Apus Systems
  Email        : info@apus-systems.com
  Version      : 0.1 Corvus Corone Cornix hacked Rudi Mantra Ry
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries and Qt resources
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
import qgis
import resources

import sys,os,stat,sqpn,edbs,tempfile

# misused for simple threadsafe and interthread debugging output
def wrn(s): QgsLogger.warning(s)  

class EdbsPlugin: 

  def __init__(self, iface):
    # save reference to the QGIS interface
    self.iface = iface
    self.params = None

  def initGui(self):  
    # create some action and connect it to self.run method 
    self.action = QAction(
      QIcon(':/plugins/EdbsPlugin/icon.png'),
      'EDBS &Import', 
      self.iface.mainWindow()
    )
    QObject.connect(self.action, SIGNAL('activated()'), self.run) 

    # add action to toolbar and menu
    #self.iface.addToolBarIcon(self.action)
    self.iface.addPluginToMenu('&EDBS ...', self.action)

  def unload(self):
    self.iface.removePluginMenu('&EDBS ...',self.action)
    #self.iface.removeToolBarIcon(self.action)

  # run the EDBS conversion plugin
  def run(self):
    if not self.params: 
      self.params = EDBSDialog(None)
      self.params.ok.clicked.connect(self.run2)
    self.params.exec_()

  def run2(self):
    d = ProgressDialog(self.params , 'EDBS Plugin')
    d.params = self.params

    # w = EDBSThread( self.iface.mainWindow() )   # (1
    w = EDBSThread( None )
    w.filename = str(self.params.fname.value())
    w.outdir = str(self.params.outdir.value())
    w.epsg = str(self.params.epsg.value())
    w.foils = str(self.params.foils.value())
    w.cb_objects = self.params.cb_objects.isChecked()
    w.cb_points = self.params.cb_points.isChecked()
    w.cb_lines = self.params.cb_lines.isChecked()
     
    c = QObject.connect
    c( w,SIGNAL('finished()'), d.jobFinished )
    c( w,SIGNAL('setLabel( PyQt_PyObject )'), d.setLabel )
    c( w,SIGNAL('setRange( PyQt_PyObject )'), d.setRange )
    c( w,SIGNAL('setValue( PyQt_PyObject )'), d.setValue )
    c( w,SIGNAL('loadLayers( PyQt_PyObject )'), d.loadLayers )
      
    # (1
    c( d,SIGNAL('terminate()'), w.terminate ) 
    #c( w,SIGNAL('finished()'), w.deleteLater );
    #c( w,SIGNAL('terminated()'), w.deleteLater );

    w.start()
    d.exec_()

class ProgressDialog(QDialog):
  def __init__( self, parent, title='Progress'):
    QDialog.__init__( self, parent )
    self.setWindowTitle(title)

    self.label = QLabel(self)
    self.label.setText('Processing')
    self.progressBar = QProgressBar(self)
    self.progressBar.setRange( 0,100 )
    self.cancelButton = QPushButton('Cancel')
    self.cancelButton.clicked.connect(self.reject)
    #self.cancelButton.setEnabled(False)
    
    self.setLayout(QVBoxLayout())
    self.layout().addWidget(self.label)
    self.layout().addWidget(self.progressBar)
    self.layout().addWidget(self.cancelButton)

  def reject(self):
    self.emit( SIGNAL( 'terminate()' ) )  
    #edbs.cancelled = True    
    QDialog.reject(self)

  def cancelThread( self ):
      pass#self.thread.stop()
  def jobFinished( self, success=True ):
      #self.cancelButton.setEnabled( True )
      self.cancelButton.setText( 'Close' )
  def setLabel( self, label):
      self.label.setText(label)
  def setRange( self, ivl ):
      self.progressBar.setRange( ivl[0], ivl[1] )
  def setValue( self, value ):
      self.progressBar.setValue(value)
  
  def loadLayers(self,shapes):
    if not self.params.cb_add.isChecked(): return
    layers = []
    bbox = None
    qgis.utils.iface.mapCanvas().setRenderFlag(False)
    for s in shapes:
      layer = qgis.utils.iface.addVectorLayer(s, s, 'ogr')
      if layer.isUsingRendererV2():
        r = layer.rendererV2()
        if r.type() == 'singleSymbol': r.symbol().setAlpha(0.5)
      if not layer.extent().isEmpty():
        if not bbox: bbox = QgsRectangle(layer.extent())
        else: bbox.unionRect(layer.extent())
      layers.append(layer)
    if bbox and self.params.cb_zoom.isChecked():
      qgis.utils.iface.mapCanvas().setExtent(bbox)
      #qgis.utils.iface.mapCanvas().refresh()
    qgis.utils.iface.mapCanvas().setRenderFlag(True)
    #return layers


class EDBSFileDialog( QFileDialog ):
  def __init__( self, parent):
    QFD = QFileDialog
    QFD.__init__( self, parent, 'Select EDBS file ' )
    self.setFileMode( QFD.ExistingFile )
    self.setOptions( QFD.ReadOnly )
    #self.setViewMode( QFD.Detail )
    self.setLabelText( QFD.FileName, 'EDBS file: ' )
    self.setLabelText( QFD.FileType, 'Filter: ' )
    self.setNameFilters(['Show all files (*)','Show EDBS files only (*.edbs *.edbs.gz)'])
  def getValue(self): return self.selectedFiles()[0]

class OutDirDialog( EDBSFileDialog ):
  def __init__( self, parent ):
    QFD = QFileDialog
    QFD.__init__( self, parent, 'Choose output directory')
    self.setFileMode( QFD.Directory )
    self.setOptions( QFD.ShowDirsOnly | QFD.HideNameFilterDetails )
    #self.setViewMode( QFD.List )
    self.setLabelText( QFD.FileName, 'Output directory: ' )
    self.setLabelText( QFD.FileType, 'Filter: ' )
    self.setNameFilters(['Show only directories (*)'])

class EPSGDialog( qgis.gui.QgsGenericProjectionSelector ):
  def getValue(self): return 'EPSG:'+str(self.selectedEpsg())

class EDBSDialog( QDialog ):
  def __init__( self, parent, title='Import EDBS'):
    QDialog.__init__( self, parent )
    self.setWindowTitle(title)

    indir = os.path.dirname(__file__)
    infile = os.path.join(indir,'testdata','edbs.ALK_Muster_EDBS_FEIN.dbout.1.001.gz')
    self.fname = InputChooser(self,'Choose EDBS File',EDBSFileDialog(self))
    self.fname.edit.setText(infile)
    self.fname.dialog.setDirectory(indir)
    self.fname.dialog.selectFile(infile)

    outdir = tempfile.gettempdir()
    self.outdir = InputChooser(self,'Output Directory',OutDirDialog(self))
    self.outdir.edit.setText(outdir)
    self.outdir.dialog.setDirectory(outdir)

    self.epsg = InputChooser(self,'Coordinate System',EPSGDialog(self))
    self.epsg.edit.setText('EPSG:31469')
    
    self.foils = InputChooser(self,'Select Foil Layers',None)
    self.foils.edit.setToolTip('Comma separated list of numbers - leave blank for all')
    self.foils.button.setToolTip('Not yet implemented')
    self.foils.button.setEnabled(False)
   
    self.cboxes = QWidget(self)
    self.cboxes.setContentsMargins(10,0,0,0)

    self.cb_objects = QCheckBox('Objects', self)
    self.cb_objects.setChecked(True)
    self.cb_points = QCheckBox('Positions', self)
    self.cb_lines = QCheckBox('Boundaries', self)
    self.cb_lines.setChecked(True)
    
    self.line = QFrame()
    self.line.setFrameShape(QFrame.HLine)
    self.line.setFrameShadow(QFrame.Sunken)
    
    self.cb_add = QCheckBox('Add layers to project', self)
    self.cb_add.setChecked(True)
    self.cb_zoom = QCheckBox('Zoom to imported layers\' extent', self)
    self.cb_zoom.setChecked(True)

    self.help = QMessageBox(self)
    self.help.setWindowTitle('About EDBS Plugin')
    self.help.setText('''
      <h3> EDBS Plugin </h3>
      <p>
      Converts data from EDBS to Shapefiles. 
      </p>
      <p>
      <a href="http://de.wikipedia.org/wiki/EDBS">EDBS</a> (Einheitliche Datenbankschnittstelle, Unified Database Interface) is some container format used mainly for interchange of federal geographic data in Germany. Other free converters are EDBSsilon, EDBS_Extra and EDBS2WKT. They differ however in how robustly they deal with different "dialects" of EDBS. So the target of this project is to overcome those issues by ease of use via QGIS integration, by simpler code via Python and GDAL and by the power of open source bundling distributed contributions.
      </p>
      <p>
      Choose EDBS file, output directory and coordinate reference system. Links and example files can be found in the plugin folder.</a>
      </p>
      <p>
      If you don\'t want to extract all layers, give a comma separated list of the foil numbers you are going to process. 
      </p>
      <p>
      With every extracted feature the original raw data will be included as attributes. For extracting additional properties out of those, add code at extractor.py.
      </p>
      <p>
      This QGIS plugin is free software released under the terms of the 
      <a 
        href="https://gnu.org/licenses/gpl.html"
        title="This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. "
      >GNU General Public Licence</a>.
      </p>

    ''')

    self.buttons = QWidget(self)
    self.helpbtn = QPushButton('Help')
    self.cancel = QPushButton('Cancel')
    self.ok = QPushButton('Import')
    self.checkReady()
    self.helpbtn.clicked.connect(self.help.exec_)
    self.cancel.clicked.connect(self.reject)

    self.fname.edit.textChanged.connect(self.checkReady)
    self.outdir.edit.textChanged.connect(self.checkReady)
    self.cb_objects.stateChanged.connect(self.checkReady)
    self.cb_points.stateChanged.connect(self.checkReady)
    self.cb_lines.stateChanged.connect(self.checkReady)

    self.buttons.setLayout(QHBoxLayout(self.buttons))
    self.buttons.layout().addWidget(self.helpbtn)
    self.buttons.layout().addWidget(self.cancel)
    self.buttons.layout().addWidget(self.ok)

    self.cboxes.setLayout(QVBoxLayout(self.cboxes))
    self.cboxes.layout().addWidget(self.cb_objects)
    self.cboxes.layout().addWidget(self.cb_points)
    self.cboxes.layout().addWidget(self.cb_lines)

    self.setLayout(QVBoxLayout(self))
    self.layout().addWidget(self.fname)
    self.layout().addWidget(self.outdir)
    self.layout().addWidget(self.epsg)
    self.layout().addWidget(self.foils)
    self.layout().addWidget(self.cboxes)
    self.layout().addWidget(self.line)
    self.layout().addWidget(self.cb_add)
    self.layout().addWidget(self.cb_zoom)
    self.layout().addWidget(self.buttons)

    self.move(0,0)
    
    self.ok.setFocus()
    #self.ok.grabKeyboard()
    #self.ok.grabMouse()


  def checkReady(self,s=None):
    x = self.cb_lines.isChecked()
    x = x or self.cb_objects.isChecked()
    x = x or self.cb_points.isChecked()
    x = x and self.fname.value() 
    x = x and self.outdir.value()
    self.ok.setEnabled(True if x else False)

class InputChooser( QWidget ):
  def __init__( self, parent, btnLabel='...', dialog=None ):
    QWidget.__init__( self, parent )
    self.dialog = dialog
    
    self.edit = QLineEdit( self )
    self.button = QPushButton( btnLabel )
    #self.button.setFixedWidth( self.button.fontMetrics().width( btnLabel ) )
        
    c = QObject.connect
    c( self.edit, SIGNAL( 'textChanged( PyQt_PyObject )' ), self, SIGNAL('fileNameChanged( PyQt_PyObject )' ) )
    c( self.button, SIGNAL( 'clicked()' ), self.chooseInput )
    
    self.setLayout(QHBoxLayout(self))
    self.layout().setMargin(0)
    self.layout().addWidget(self.edit)
    self.layout().addWidget(self.button)
    
  def chooseInput(self):
    if not self.dialog: return
    if self.dialog.exec_():
      txt = self.dialog.getValue()
      if not txt: txt = ''
      self.edit.setText( txt )
      self.emit( SIGNAL('inputChanged( PyQt_PyObject )'), txt)
    #setFocusProxy( edit )

  def value(self): return self.edit.text()
  #def setValue(self,val): self.edit.setText(str(val))


class EDBSThread( QThread ):

  # progress interface
  def progress_label(self,s):
    self.emit( SIGNAL( 'setLabel( PyQt_PyObject )' ), s )
  def progress_total(self,n):
    self.total = n
    self.current = 0 
  def progress_steps(self,dn):
    self.current += dn
    now = int(self.current*100/self.total)
    if self.last != now:
      #wrn('EDBSThread.steps emitting {0},{1},{2} {3},{4}'.format(self.current, self.total, n, self.last,now))
      self.emit( SIGNAL( 'setValue( PyQt_PyObject )' ), now )
      self.last = now
  

  def run(self):
    sqpn.progress = self

    for f in [self.filename]:
      message = 'Processing "{0}"'.format(os.path.realpath(f))
      self.emit( SIGNAL( 'setLabel( PyQt_PyObject )' ), message )
      self.current = self.last = 0 
      self.total = os.stat(f)[stat.ST_SIZE]
      shapes = sqpn.main(f,self.outdir,self.epsg,self.foils,self.cb_objects,self.cb_points,self.cb_lines)
      self.emit( SIGNAL( 'loadLayers( PyQt_PyObject )' ), shapes )
      self.progress_label('Conversion done. ')

