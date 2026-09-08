/**********************************************************************
 * Sultan Marshes - open-water reality check -> exports ONE CSV.
 * Run, then in the Tasks tab click Run on "SultanMarshes_water_check";
 * download sultan_water_areas.csv and send it back.
 **********************************************************************/
// ---- AOI: same Ramsar wetland as the paper ----
var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons');
var cand = wdpa.filter(ee.Filter.and(
    ee.Filter.stringContains('NAME','Sultan'), ee.Filter.eq('ISO3','TUR')));
var ramsar = cand.filter(ee.Filter.stringContains('DESIG_ENG','Ramsar'));
var aoi = ee.Geometry(ee.Algorithms.If(ramsar.size().gt(0),
            ramsar.geometry().dissolve(1), cand.geometry().dissolve(1)));
Map.centerObject(aoi, 11);
print('AOI area km2:', aoi.area(1).divide(1e6));   // sanity check ~176
var PXA = ee.Image.pixelArea().divide(1e6);
var feats = [];
function push(src, metric, yr, mask){
  var v = ee.Number(mask.updateMask(mask).multiply(PXA)
    .reduceRegion({reducer: ee.Reducer.sum(), geometry: aoi, scale: 30, maxPixels: 1e13})
    .values().get(0));
  feats.push(ee.Feature(null, {source: src, metric: metric, year: yr,
                               water_km2: v}));
}
// ---- (1) JRC Global Surface Water (independent benchmark) ----
var gsw = ee.ImageCollection('JRC/GSW1_4/YearlyHistory');
[1984,2000,2015,2021].forEach(function(y){
  var wc = gsw.filter(ee.Filter.eq('year',y)).first().select('waterClass');
  push('JRC','permanent', y, wc.eq(3));
  push('JRC','perm+seasonal', y, wc.gte(2));
});

// ---- (2) Landsat MNDWI water, SPRING vs LATE-SUMMER ----
function maskL2(img){ var qa=img.select('QA_PIXEL');
  var bad=qa.bitwiseAnd(1<<1).neq(0).or(qa.bitwiseAnd(1<<3).neq(0))
    .or(qa.bitwiseAnd(1<<4).neq(0)).or(qa.bitwiseAnd(1<<5).neq(0));
  return img.updateMask(bad.not()); }
function mndwi(img, oli){ var b = oli ? ['SR_B3','SR_B6'] : ['SR_B2','SR_B5'];
  var s = maskL2(img).select(b).multiply(0.0000275).add(-0.2);
  return s.normalizedDifference([b[0],b[1]]).rename('MNDWI'); }
function water(y0,y1,m0,m1){
  function c(id,oli){ return ee.ImageCollection(id).filterBounds(aoi)
    .filter(ee.Filter.calendarRange(y0,y1,'year'))
    .filter(ee.Filter.calendarRange(m0,m1,'month')).map(function(i){return mndwi(i,oli);}); }
  return c('LANDSAT/LT05/C02/T1_L2',false).merge(c('LANDSAT/LE07/C02/T1_L2',false))
    .merge(c('LANDSAT/LC08/C02/T1_L2',true)).merge(c('LANDSAT/LC09/C02/T1_L2',true))
    .median().gt(0.0); }   // MNDWI>0 = water
[[1984,1986],[1998,2002],[2013,2017],[2023,2025]].forEach(function(e){
  push('Landsat','spring(Apr-Jun) MNDWI>0', e[0], water(e[0],e[1],4,6));
  push('Landsat','summer(Aug-Sep) MNDWI>0', e[0], water(e[0],e[1],8,9));
});

Export.table.toDrive({
  collection: ee.FeatureCollection(feats),
  description: 'SultanMarshes_water_check',
  folder: 'GEE_SultanMarshes',
  fileNamePrefix: 'sultan_water_areas',
  fileFormat: 'CSV',
  selectors: ['source','metric','year','water_km2']
});
