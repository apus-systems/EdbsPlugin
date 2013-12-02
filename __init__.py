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
def name(): 
  return 'EDBS plugin' 
def description():
  return 'conversion of EDBS data to polygon, line and point layers'
def version(): 
  return 'Version 0.1' 
def qgisMinimumVersion():
  return '1.8'
def classFactory(iface): 
  # load EdbsPlugin class from file EdbsPlugin
  from EdbsPlugin import EdbsPlugin 
  return EdbsPlugin(iface)
