from math import pi as PI
from osgeo import osr,ogr
import sqpn, re,gzip, types, itertools
filter = itertools.ifilter   #  filter is lazy only in Python >= 3

# parser/tokenizer
class token:
  def __init__(self,tag,len): 
    self.tag = tag
    self.len = len
  def parse(self,s,i,data): # (string, position, data) -> next position
    data[self.tag] = s[i:i+self.len]
    return i+self.len

# sequence of tokens
class token_seq(token):
  def __init__(self,seq):
    self.seq = []
    for p in seq:
      self.seq.append(p if isinstance(p,token) else token(p[0],p[1]))

  def parse(self,s,i,data): 
    for p in self.seq:
      i = p.parse(s,i,data)
    return i

# repeater of token (sequence)
class ulob(token):
  def __init__(self,tag,tok): 
    self.tag = tag
    self.tok = tok if isinstance(tok,token) else token_seq(tok)

  def parse(self,s,i,data): 
    repeat = int(s[i:i+4])
    i += 4
    if not repeat: return i
    d = data[self.tag] = []
    for k in range(repeat):
      d.append({})
      i = self.tok.parse(s,i,d[-1])
    return i


point = token_seq([
  ['num_bezirk' ,  8 ],
  ['koordinate' , 12 ]
])

ulob0000 = ulob('grundrisskennzeichen',[point,['pruefzeichen',1]])
ulob1000 = ulob('liniengeometrie',[point,['geometrieart',2]])
ulob1100 = ulob('linienfunktion',[
  ['folie'                , 3 ],
  ['objektart'            , 4 ],
  ['objektnr_r'           , 7 ],
  ['objektnr_l'           , 7 ],
  ['objektteilnr_r'       , 3 ],
  ['objektteilnr_l'       , 3 ],
  ['linienteilung_r'      , 1 ],
  ['linienteilung_l'      , 1 ]
])
ulob1110 = ulob('fachparameter',[
  ['art'     , 1],
  ['kennung' , 1],
  ['wert'    , 1]
]) #  lengths variabel depending on object -> used only in ATKIS
ulob1200 = ulob('lageparameter',point)


ulob2000 = ulob('objektfunktion',[
  ['folie'                , 3 ],
  ['objektart'            , 4 ],
  ['aktualitaet'          , 2 ],
  ['objekttyp'            , 1 ],
  ['objektnr'             , 7 ],
  ['modelltyp'            , 2 ],
  ['entstehungsdatum'     , 6 ],
  ['veraenderungskennung' , 1 ]
])
ulob2100 = ulob('objektinformation',[
  ['infoart'      ,  2 ],
  ['kartentyp'    ,  2 ],
  ['objektart'    ,  6 ],
  ['information'  , 33 ],
  ['geometrieart' ,  2 ],
  ['objektteilnr' ,  3 ]
])
ulob2110 = ulob('geometrie',point)


ulob110f = ulob('u110f',[ulob1100,ulob1110])
ulob210f = ulob('u210f',[ulob2100,ulob2110]) 
ulob100f = ulob('u100f',[ulob1000,ulob110f,ulob1200])
ulob200f = ulob('u200f',[ulob2000,ulob210f])
ulobnn = ulob('nn',[ulob0000,ulob100f,ulob200f])


# define some onLineParsed handlers

# strangely enough limbach coordinates are mixed 31468,31469
epsg31468 = osr.SpatialReference()
epsg31468.ImportFromEPSG(31468)
epsg31469 = osr.SpatialReference()
epsg31469.ImportFromEPSG(31469)

# 31468 -> 31469
T_limbach = osr.CoordinateTransformation(epsg31468,epsg31469) 

def fix_limbach(data):
  x,y = data['xy']
  if x<=5000000:
    p=ogr.Geometry(ogr.wkbPoint)
    p.SetPoint(0,x,y)
    p.Transform(T_limbach)
    data['xy_old'] = [x,y]
    data['xy'] = [p.GetX(),p.GetY()]

def process_point(p):
  if p[0:2] == 'TT':
    phi = float(p[2:7])
    phi *= PI/20000  # cgon (s. wiki/Gon)
    phi = PI/2 - phi
    if phi < 0 : phi += 2*PI
    return { 'phi': phi }
  x = p[0:2] + p[4:6] + p[8:11] + '.' + p[11:14]
  y = p[2:4] + p[6:8] + p[14:17] + '.' + p[17:20]
  data = { 'xy': [float(x),float(y)] }
  if sqpn.FIX_LIMBACH: fix_limbach(data)
  return data

def point_parse(self,s,i,data):
  i = token_seq.parse(self,s,i,data)
  data.update ( process_point(data['num_bezirk']+data['koordinate']) )
  return i

# see http://docs.python.org/2/howto/descriptor.html
# alternative to testing for an instance callback function in token_seq.parse 
# or subclassing
point.parse = types.MethodType(point_parse,point)


#data = {}

#s = '46560557143987913978'
#token('ppp',7).parse(s,0,data)
#point.parse(s,0,data)

#s = '0003465605571439879139784656055714398791397846560557143987913978'
#ulob2110.parse(s,0,data)

#s = '00010001465605571439879139788000000010001001023305FP012PR7  041123 0001000113K4  0233SF14378400000000900000200        51   000146560557143987913978'
#s = '00010001465604589606710278465000100014656055711894587832411000100010010233       P012PR7       0000000000000'
#print ulobnn.parse(s,0,data), len(s)

#print data

def edbsProcessor(lines):
  for line in lines:
    if re.match('EDBS.{8}(FEIN|BSPE)',line): 
      l = line.strip()
      folge = l[22]
        
      if folge in [' ','A']: 
        info = l[36:]
      else: 
        info += l[36:]
       
      if folge in [' ','E']:
        #print l[16:22]
        data = {'satznr':l[16:22]}
        read = ulobnn.parse(info,0,data)

        if read != len(info):
          #w#print read, len(info), data
          break
          
        #print data         # print data in python text format
        yield data
    
    sqpn.progress_steps(len(line))

def evalProcessor(lines):
  for line in lines: 
    yield eval(line.strip())
    sqpn.progress_steps(len(line))

# reads in ALL data from raw edbs or python text 
def read_lines(filename='fein.gz', lineProcessor=edbsProcessor):

  for type in 'gz','ascii':
    try:
      fileopen = gzip.open if type == 'gz' else open
      f = fileopen(filename,'rb') 
      #lines = filter(None,(l.strip() for l in f))
      lines = (l for l in f)
      return list(lineProcessor(lines))
    except IOError as err:
      if str(err) != 'Not a gzipped file': raise


def read_edbs(filename='fein.gz'): 
  return read_lines(filename, edbsProcessor)

def read_txt(filename='db.txt.gz'):
  return read_lines(filename, evalProcessor)


def write_txt(db,filename='db.txt.gz'):
  f = gzip.open(filename,'wb')
  for data in db:
    f.write(str(data)+'\n')
  f.close()


# just to see that read/write_txt is much much faster, why ???
# anyway reading edbs is still fastest
def pickle_db(db,filename='db.pickle.gz'):
  f = gzip.open(filename,'wb')
  pickle.dump(db,f)
  f.close()

def unpickle_db(filename='db.pickle.gz'):
  f = gzip.open(filename,'rb')
  db = pickle.load(f)
  f.close()
  return db


