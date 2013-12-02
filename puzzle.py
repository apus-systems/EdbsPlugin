def puzzle_lines(lines):
  polylines=[]
  for l in lines:
    ok = False
    for p in polylines:
      if p[-1]==l[0]:
        ok = True
        p.append(l[1])
        for p2 in polylines:
          if p!=p2:
            if l[1]==p2[0]:
              p.append(p2)
              polylines.remove(p2)
              break
        break
      elif l[1]==p[0]:
        ok = True
        p.insert(0,l[0])
        for p2 in polylines:
          if p!=p2:
            if l[0]==p2[-1]:
              p2.append(p)
              polylines.remove(p)
              break
        break
    
    if not ok: polylines.append(l)

  return polylines


def puzzle_db(db):
  db['polygons'] = complete = {}
  db['polylines'] = incomplete = {}

  for objnr,obj in db['objects'].items():
    if objnr in db['lines']:
      poly = puzzle_lines(db['lines'][objnr])
    else:
      #w#print 'no lines for '+objnr
      poly = []

    closed = True
    for p in poly:
      if len(p)<3 or p[0] != p[-1]:
        closed = False
        break
    if closed: 
      complete[objnr] = [obj,poly]
      if len(poly)>1:
        pass
        #w#print '{0}-ring object {1}'.format(len(poly),objnr)
        #print poly
    else:
      incomplete[objnr] = [obj,poly]
      #w#print 'incomplete object '+objnr
      #w#print poly


