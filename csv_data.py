import memoize, gzip,csv,os, sys,types

class _csv_data(types.ModuleType):

  def __init__(self,name):
    types.ModuleType.__init__(self,name)
    self.path = os.path.dirname(__file__)

  @memoize 
  def read_nutzungsarten(self):
    nutzungsarten = {}
    f = open(os.path.join(self.path,'csv','nutzungsart.csv'),'rb')
    for d in csv.reader(f,delimiter=';'):
      nutzungsarten[d[1]] = d
    return nutzungsarten

  @memoize 
  def read_gemarkungen(self):
    gemarkungen = {}
    #w#print self.path
    f = gzip.open(os.path.join(self.path,'csv','gmk_sachsen.csv.gz'),'rb')
    f.next()
    for d in csv.reader(f,delimiter=';'):
      gemarkungen[d[2]] = d
    return gemarkungen

  @memoize 
  def read_gemeinden(self):
    gemeinden = {}
    verbaende = {}
    laender = {}
    f = gzip.open(os.path.join(self.path,'csv','AuszugGV1QAktuell.csv.gz'),'rb')
    f.next()
    for d in csv.reader(f,delimiter=';'):
      if d[6]:
        schluessel = d[2]+d[3]+d[4]+d[6]
        if schluessel in gemeinden:
          pass
          #w#print 'duplicate key {0} : {1}'.format(schluessel,d)
        gemeinden[schluessel] = d
      elif d[2] and d[3] and d[4]:
        schluessel = d[2]+d[3]+d[4]
        verbaende[schluessel] = d
      elif d[2] and not d[3] and not d[4]:
        laender[d[2]] = d
      #else:
      #  print d

    return [gemeinden,verbaende,laender]

  @property
  def nutzungsarten(self): return self.read_nutzungsarten()

  @property
  def gemarkungen(self): return self.read_gemarkungen()

  @property
  def gemeinden(self): return self.read_gemeinden()[0]

  @property
  def verbaende(self): return self.read_gemeinden()[1]

  @property
  def laender(self): return self.read_gemeinden()[2]

csv_data = _csv_data(__name__)
sys.modules[__name__] = csv_data
import gzip,csv,os   # reimport into module namespace somehow cleared by hack above


