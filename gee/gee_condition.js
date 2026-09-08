/**********************************************************************
 * Sultan Marshes - ecological condition, v2 (for Figure 6)
 * Exports the CONTINUOUS Ecological Condition Index (ECI, 0..1) per epoch,
 * so the 5 class breaks can be calibrated locally (no more GEE runs).
 *
 * Fix vs v1: open water now scores as GOOD condition. ECI rewards surface
 * water and wet vegetation and penalises bare soil; NDVI no longer drags
 * open water down.
 *   wet   = mean( norm(NDWI), norm(MNDWI), norm(NDMI) )   surface water/moisture
 *   green = norm(NDVI)                                    wetland vegetation vigour
 *   bare  = norm(BSI)                                     bare-soil fraction
 *   ECI   = 0.60*wet + 0.25*green + 0.15*(1 - bare)       -> 0..1  (higher = better)
 **********************************************************************/

// ---- AOI (WDPA Ramsar, Turkey only) --------------------------------------
var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons');
var cand = wdpa.filter(ee.Filter.and(
    ee.Filter.stringContains('NAME', 'Sultan'), ee.Filter.eq('ISO3', 'TUR')));
var ramsar = cand.filter(ee.Filter.stringContains('DESIG_ENG', 'Ramsar'));
var aoi = ee.Geometry(ee.Algorithms.If(ramsar.size().gt(0),
            ramsar.geometry().dissolve(1), cand.geometry().dissolve(1)));
Map.centerObject(aoi, 11);
print('AOI area (km2):', aoi.area(1).divide(1e6));

var EPOCHS = [{label:'1984',y0:1984,y1:1986},{label:'2000',y0:1998,y1:2002},
              {label:'2015',y0:2013,y1:2017},{label:'2025',y0:2023,y1:2025}];
var MS = 8, ME = 9, MAXC = 60;

function maskL2(img){
  var qa=img.select('QA_PIXEL');
  var bad=qa.bitwiseAnd(1<<1).neq(0).or(qa.bitwiseAnd(1<<2).neq(0))
    .or(qa.bitwiseAnd(1<<3).neq(0)).or(qa.bitwiseAnd(1<<4).neq(0))
    .or(qa.bitwiseAnd(1<<5).neq(0));
  return img.updateMask(bad.not()).updateMask(img.select('QA_RADSAT').eq(0));
}
function idx(sr){
  return ee.Image.cat([
    sr.normalizedDifference(['nir','red']).rename('NDVI'),
    sr.normalizedDifference(['green','nir']).rename('NDWI'),
    sr.normalizedDifference(['green','swir1']).rename('MNDWI'),
    sr.normalizedDifference(['nir','swir1']).rename('NDMI'),
    sr.expression('((S1+R)-(N+B))/((S1+R)+(N+B))',
      {S1:sr.select('swir1'),R:sr.select('red'),N:sr.select('nir'),B:sr.select('blue')})
      .rename('BSI')]).copyProperties(sr,['system:time_start']);
}
function pTM(i){return idx(ee.Image(maskL2(i).select(
  ['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B7'],
  ['blue','green','red','nir','swir1','swir2']).multiply(0.0000275).add(-0.2)));}
function pOLI(i){return idx(ee.Image(maskL2(i).select(
  ['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],
  ['blue','green','red','nir','swir1','swir2']).multiply(0.0000275).add(-0.2)));}
function comp(y0,y1){
  function b(id,p){return ee.ImageCollection(id).filterBounds(aoi)
    .filter(ee.Filter.calendarRange(y0,y1,'year'))
    .filter(ee.Filter.calendarRange(MS,ME,'month'))
    .filter(ee.Filter.lte('CLOUD_COVER_LAND',MAXC)).map(p);}
  return b('LANDSAT/LT04/C02/T1_L2',pTM).merge(b('LANDSAT/LT05/C02/T1_L2',pTM))
    .merge(b('LANDSAT/LE07/C02/T1_L2',pTM)).merge(b('LANDSAT/LC08/C02/T1_L2',pOLI))
    .merge(b('LANDSAT/LC09/C02/T1_L2',pOLI)).median();
}
function norm(x,lo,hi){return x.subtract(lo).divide(hi-lo).clamp(0,1);}
function eci(ix){
  var wet=ee.Image.cat([norm(ix.select('NDWI'),-0.4,0.5),
                        norm(ix.select('MNDWI'),-0.4,0.6),
                        norm(ix.select('NDMI'),-0.3,0.4)]).reduce(ee.Reducer.mean());
  var green=norm(ix.select('NDVI'),0.1,0.6);
  var bare =norm(ix.select('BSI'),0.0,0.4);
  return wet.multiply(0.60).add(green.multiply(0.25))
           .add(ee.Image(1).subtract(bare).multiply(0.15)).clamp(0,1).rename('ECI');
}

var bands=[];
EPOCHS.forEach(function(e){
  var E=eci(comp(e.y0,e.y1)).clip(aoi).rename('ECI_'+e.label);
  bands.push(E);
  // percentiles to help set class breaks
  print(e.label+' ECI p[10,25,50,75,90]:', E.reduceRegion({
    reducer:ee.Reducer.percentile([10,25,50,75,90]),geometry:aoi,scale:30,maxPixels:1e13}));
  Map.addLayer(E,{min:0.15,max:0.75,
    palette:['d62828','ef7d34','f4c430','7cb342','1a7a3f']},'ECI '+e.label,e.label==='2025');
});

Export.image.toDrive({
  image: ee.Image.cat(bands).toFloat(),
  description:'SultanMarshes_ECI_epochs',
  folder:'GEE_SultanMarshes',
  fileNamePrefix:'sultan_ECI_4epochs',
  region:aoi, scale:30, crs:'EPSG:32636', maxPixels:1e13
});
// Run -> start the single export -> send sultan_ECI_4epochs.tif back.
