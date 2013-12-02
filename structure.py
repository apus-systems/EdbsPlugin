import sqpn

def add_line(lines,objnr,satz,reverse=False):

  p0 = satz['xy0']
  p1 = satz['xy1']
  if reverse: p0,p1=p1,p0
  if not objnr in lines: lines[objnr]=[]
  lines[objnr].append([p0,p1])

def structurize(saetze):

  lines = {}
  objects = {}
  for s in saetze:
    sqpn.progress_steps(1)

    if 'u100f' in s['nn'][0]:
      data = s['nn'][0]['u100f'][0]['u110f'][0]['linienfunktion'][0]
      xy0 = s['nn'][0]['grundrisskennzeichen'][0]['xy']
      xy1 = s['nn'][0]['u100f'][0]['liniengeometrie'][0]['xy']

      s['xy0'] = xy0
      s['xy1'] = xy1
      s['data'] = data
      
      # objektart 0242: 
      # nicht darzustellende Linie zur Objektdefinition,
      # zB. zur Verbindung zwischen outerRing und innerRing
      # (in diesem Fall gilt auch objektnr_l==objectnr_r)
      if data['objektart'] != '0242':  
        if data['objektnr_l']:
          add_line(lines,data['objektnr_l'],s)
        if data['objektnr_r']:
          add_line(lines,data['objektnr_r'],s,True)
    
    
    elif 'u200f' in s['nn'][0]:
      data = s['nn'][0]['u200f'][0]['objektfunktion'][0]
      xy = s['nn'][0]['grundrisskennzeichen'][0]['xy']
      objnr = data['objektnr']

      s['objnr'] = objnr
      s['xy'] = xy
      s['data'] = data

      if objnr in objects:
        pass
        #w#print 'objnr in '+s['satznr']+' duplicates '+objects[objnr]['satznr']
      else:
        objects[objnr] = s
  
  return {'saetze':saetze, 'lines':lines, 'objects':objects}


