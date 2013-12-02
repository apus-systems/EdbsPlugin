import csv_data,re,sys
from sqpn import RAWLINES
from osgeo import ogr

class extractor:
  def create_fields(self,layer):
    for i in range(RAWLINES):
      layer.CreateField(ogr.FieldDefn('_rawpy{0:04}'.format(i), ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('folie', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('objektart', ogr.OFTString))

  def set_fields(self,feature,satz):
    rawlines = re.findall('.{1,80}',str(satz['nn']))
    rawcount = min(RAWLINES,len(rawlines))
    for i in range(rawcount):
      feature.SetField('_rawpy{0:04}'.format(i), rawlines[i] )

    data = satz['data']
    feature.SetField( 'folie', data['folie'] )
    feature.SetField( 'objektart', data['objektart'] )

class extractor_line(extractor):
  def create_fields(self,layer):
    extractor.create_fields(self,layer)
    layer.CreateField(ogr.FieldDefn('objektnr_l', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('objektnr_r', ogr.OFTString))

  def set_fields(self,feature,satz):
    extractor.set_fields(self,feature,satz)
    feature.SetField( 'objektnr_l', satz['data']['objektnr_l'] )
    feature.SetField( 'objektnr_r', satz['data']['objektnr_r'] )


class extractor_object(extractor):
  def create_fields(self,layer):
    extractor.create_fields(self,layer)
    layer.CreateField(ogr.FieldDefn('objektnr', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('position_x', ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn('position_y', ogr.OFTReal))

  def set_fields(self,feature,satz):
    extractor.set_fields(self,feature,satz)
    feature.SetField( 'objektnr', satz['data']['objektnr'] )
    feature.SetField( 'position_x', satz['xy'][0] )
    feature.SetField( 'position_y', satz['xy'][1] )


class extractor_nutzung:
  def __init__(self):
    self.nutzungsarten = csv_data.nutzungsarten

  def create_fields(self,layer):
    layer.CreateField(ogr.FieldDefn('nutzung', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('nutz_txt', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('nutz_icon', ogr.OFTString))
    #layer.CreateField(ogr.FieldDefn('nutz_col', ogr.OFTString))

  def set_fields(self,feature,satz):
    art = int(satz['data']['objektart'])
    nosymbol = art%10 > 0
    art = str(art/10)
    
    if art in self.nutzungsarten:
      feature.SetField( 'nutzung', self.nutzungsarten[art][2] )
      feature.SetField( 'nutz_txt', self.nutzungsarten[art][0] )
    
    feature.SetField( 'nutz_icon', 'N' if nosymbol else 'J' )
    #feature.SetField( 'nutz_col', self.nutzungsarten[art][4] )


class extractor_flur:
  def __init__(self):
    self.gemarkungen = csv_data.gemarkungen

  def create_fields(self,layer):
    layer.CreateField(ogr.FieldDefn('land', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('land_txt', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('gemeinde', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('gemein_txt', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('gemarkung', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('gemark_txt', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('flurnr', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('flurzaehlr', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('flurnenner', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('flur_txt', ogr.OFTString))

  def set_fields(self,feature,satz):
    # K-5/05 Teil C Anhang 2, Seite 8
    s = satz['nn'][0]['u200f'][0]['u210f'][0]['objektinformation'][0]['information']
    #s = satz['info']['information']

    land, gemarkung, flur, zaehler, nenner = s[2:4], s[4:8], s[8:12], s[12:18], s[18:23]
    land_txt, gemeinde, gemein_txt, gemark_txt = '','','',''

    if land == '14':
      land_txt = 'Sachsen'
      gemeinde = self.gemarkungen[gemarkung][0]
      gemein_txt = self.gemarkungen[gemarkung][1]
      gemark_txt = self.gemarkungen[gemarkung][3]
    else: # fallback
      try: 
        land_txt = csv_data.laender[land][7]
        gemeinde = land+bezirk+kreis+gemeinde
        gemein_txt = csv_data.gemeinden[gemeinde][7]
      except KeyError: pass

    flur_text = zaehler.lstrip(' 0')
    if nenner.lstrip(' 0'): flur_text += '/'+nenner.lstrip(' 0')

    feature.SetField('land', land)
    feature.SetField('land_txt', land_txt)
    feature.SetField('gemeinde', gemeinde)
    feature.SetField('gemein_txt', gemein_txt)
    feature.SetField('gemarkung', gemarkung)
    feature.SetField('gemark_txt', gemark_txt)
    feature.SetField('flurnr', flur)
    feature.SetField('flurzaehlr', zaehler)
    feature.SetField('flurnenner', nenner)
    feature.SetField('flur_txt', flur_text)


class extractor_gebaeude:
  def __init__(self):
    self.gemeinden = csv_data.gemeinden
    self.laender = csv_data.laender

  def create_fields(self,layer):
    layer.CreateField(ogr.FieldDefn('land', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('land_txt', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('kreis', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('gemeinde', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('gemein_txt', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('strasse', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('hausnr', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('nummer', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('zusatz', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('lfd_nr', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('kennung', ogr.OFTString))
    layer.CreateField(ogr.FieldDefn('str_txt', ogr.OFTString))

  def set_fields(self,feature,satz):
    # K-5/05 Teil C Anhang 2, Seite 8
    infos = satz['nn'][0]['u200f'][0]['u210f']
    for info in infos:
      if info['objektinformation'][0]['information'][0:2] == 'HA':
        break
      
    s = info['objektinformation'][0]['information']

    land, kreis, gemeinde, strasse, nummer, zusatz, kennung, lfd_nr = s[2:4], s[4:7], s[7:10], s[10:15], s[15:19], s[19:23], s[23:24], s[24:26]

    schluessel = land+kreis+gemeinde
    land_txt = self.laender[land][7] if land in self.laender else ''
    gemein_txt = self.gemeinden[schluessel][7] if schluessel in self.gemeinden else ''
    nummer = nummer.lstrip(' 0')
    zusatz = zusatz.lstrip(' ')

    nummer_txt = nummer
    if zusatz: nummer_txt += ' '+zusatz

    if kennung != 'P': lfd_nr = kennung + lfd_nr
    lfd_nr = lfd_nr.lstrip(' 0')
    str_txt = ''  # TODO

    feature.SetField('land', land)
    feature.SetField('land_txt', land_txt)
    feature.SetField('kreis', kreis)
    feature.SetField('gemeinde', gemeinde)
    feature.SetField('gemein_txt', gemein_txt)
    feature.SetField('strasse', strasse)
    feature.SetField('hausnr', nummer_txt)
    feature.SetField('nummer', nummer)
    feature.SetField('zusatz', zusatz)
    feature.SetField('lfd_nr', lfd_nr)
    feature.SetField('kennung', kennung)
    feature.SetField('str_txt', str_txt)

defaultExtractors = {
  '001': extractor_flur(),
  '021': extractor_nutzung(),
  '011': extractor_gebaeude() # None
}


