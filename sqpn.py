"""
/***************************************************************************
  Name         : sqpn - Unified DataBase Scanner 
  Description  : conversion of EDBS data to polygon, line and point layers
  Date         : 2013-06-30 
  Copyright    : (c) 2013, Apus Systems, GNU GPL licenced
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

# settings
FIX_LIMBACH = True   # workaround for mixed CRS in our testdata
PATH = '/dev/shm/'
FORMAT = 'SHP'
RAWLINES = 20 

from osgeo import ogr,osr
import os

import edbs
from edbs import *
from structure import *
from puzzle import *
from extractors import *

progress = None
def progress_label(s):
  if progress: progress.progress_label(s)
def progress_total(n):
  if progress: progress.progress_total(n)
def progress_steps(dn):
  if progress: progress.progress_steps(dn)

def getFolie(satz):
  x = satz['nn'][0]
  if 'u100f' in x :
    y = x['u100f'][0]['u110f'][0]['linienfunktion']
  else:
    y = x['u200f'][0]['objektfunktion']
  return y[0]['folie']

def filter_folien(saetze,folien):
  return [s for s in saetze if getFolie(s) in folien]


def dataSource(filename,fileformat=FORMAT):
  # create the datasource
  if fileformat == 'SHP':    # ESRI Shapefile 
    outFn = filename+'.shp'
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outFn):
      driver.DeleteDataSource(outFn)
  else:       # GML
    outFn = filename+'.gml'
    driver = ogr.GetDriverByName('GML')
    if os.path.exists(outFn):
      os.unlink(outFn)
  
  dataSource = driver.CreateDataSource(outFn)
  return dataSource


def save_lines(db,filename,extractor=None,proj=None,fileformat=FORMAT):

  dataSrc = dataSource(filename,fileformat)
  geomType = ogr.wkbLineString
  lineExtractor = extractor_line()

  # create a layer 
  layer = dataSrc.CreateLayer('line', geom_type=geomType, srs=proj)
  lineExtractor.create_fields(layer)
  featureDefn = layer.GetLayerDefn()

  # and its features
  for s in db['saetze']:
    sqpn.progress_steps(1)
    
    if 'u100f' in s['nn'][0]:
      data = s['data']
      xy0 = s['xy0']
      xy1 = s['xy1']

      feature = ogr.Feature(featureDefn)
      feature.SetFID( int(s['satznr']) )
      
      line = ogr.Geometry(geomType)
      line.SetPoint(0,xy0[0],xy0[1])
      line.SetPoint(1,xy1[0],xy1[1])
      feature.SetGeometry(line)
      line.Destroy()
      
      lineExtractor.set_fields(feature,s) 

      layer.CreateFeature(feature)
      feature.Destroy()

  fname = dataSrc.GetName()
  dataSrc.Destroy()
  return fname

def save_objects(db,filename,extractor=None,proj=None,fileformat=FORMAT):

  dataSrc = dataSource(filename,fileformat)
  geomType = ogr.wkbPolygon
  objectExtractor = extractor_object()

  layer = dataSrc.CreateLayer('poly', geom_type=geomType, srs=proj)
  objectExtractor.create_fields(layer)
  if extractor: extractor.create_fields(layer)
  featureDefn = layer.GetLayerDefn()

  for objnr,[satz,polygons] in db['polygons'].items():
    sqpn.progress_steps(1)
  
    feature = ogr.Feature(featureDefn)
    poly = ogr.Geometry(geomType)
    ring = ogr.Geometry(ogr.wkbLinearRing)

    for p in polygons:
      ring.Empty()
      for l in p:
        ring.AddPoint(l[0],l[1])
      poly.AddGeometry(ring)

    ring.Destroy()
    poly.CloseRings()

    feature.SetFID( int(satz['satznr']) )
    feature.SetGeometry(poly)
    poly.Destroy()
    
    objectExtractor.set_fields(feature,satz)
    if extractor: extractor.set_fields(feature,satz)
    
    layer.CreateFeature(feature)
    feature.Destroy()
  
  fname = dataSrc.GetName()
  dataSrc.Destroy()
  return fname

def save_points(db,filename,extractor=None,proj=None,fileformat=FORMAT):

  dataSrc = dataSource(filename,fileformat)
  geomType = ogr.wkbPoint
  objectExtractor = extractor_object()

  layer = dataSrc.CreateLayer('poly', geom_type=geomType,srs=proj)
  objectExtractor.create_fields(layer)
  if extractor: extractor.create_fields(layer)
  featureDefn = layer.GetLayerDefn()

  for objnr,[satz,polygons] in db['polygons'].items():
    sqpn.progress_steps(1)

    feature = ogr.Feature(featureDefn)
    point = ogr.Geometry(geomType)
    
    xy=satz['xy']
    point.SetPoint(0,xy[0],xy[1])

    feature.SetFID( int(satz['satznr']) )
    feature.SetGeometry(point)
    point.Destroy()
    
    objectExtractor.set_fields(feature,satz)
    if extractor: extractor.set_fields(feature,satz)
    
    layer.CreateFeature(feature)
    feature.Destroy()
  
  fname = dataSrc.GetName()
  dataSrc.Destroy()
  return fname


def main(edbsfile, path=PATH, epsg='EPSG:31469', folien='1,11,21', cb_objects=True, cb_points=False, cb_lines=False):
  #global saetze, s, db, extractors  #  for debugging in python console
  filename = os.path.basename(edbsfile)
  #w#print 'path =',path

  proj = osr.SpatialReference()
  proj.ImportFromEPSG(31469)

  shapes=[]
  saetze = read_edbs(edbsfile)


  if not folien:
    folien = list(set(getFolie(s) for s in saetze))
  else:
    folien = list(set('{0:03d}'.format(int(f)) for f in folien.split(',')))

  #w#print folien

  extractors = dict((f,None) for f in folien)
  extractors.update(defaultExtractors)
 
  # TODO
  # if config:
  #  '001'   'projection.prj'  extractor  'style.qml'

  s,db = {},{}
  #for folie in ['001','021','011']:
  for folie in folien:
    s[folie] = filter_folien( saetze, [folie] )
    
    progress_label('Processing foil {0} of {1}'.format(folie,filename))
    progress_total(len(s[folie]))
    db[folie] = structurize( s[folie] )
    puzzle_db( db[folie] )

    if cb_objects:
      fname = os.path.join(path,'o'+folie)
      progress_label('Saving {0} objects to {1}'.format(folie,fname))
      progress_total(len(db[folie]['polygons']))
      shapes.append( save_objects( db[folie], fname, extractors[folie], proj ) )
    if cb_points:
      fname = os.path.join(path,'p'+folie)
      progress_label('Saving {0} points to {1}'.format(folie,fname))
      progress_total(len(db[folie]['polygons']))
      shapes.append( save_points( db[folie], fname, extractors[folie], proj ) )
    if cb_lines:
      fname = os.path.join(path,'l'+folie)
      progress_label('Saving {0} boundaries to {1}'.format(folie,fname))
      progress_total(len(db[folie]['saetze']))
      shapes.append( save_lines( db[folie], fname, extractors[folie], proj ) )

    #w#print

  return shapes
 
