/**********************************************************************
 * Sultan Marshes - driver stack for Figure 8 (SHAP)
 * Exports one per-pixel multiband raster (predictors + label) over the
 * Ramsar wetland, so a Random Forest can be trained and SHAP computed
 * LOCALLY (real feature importance, no fabricated Table 5).
 *
 * Bands:
 *   Climate (TerraClimate, growing-season mean 1984-2025):
 *     pr, pet, def (water deficit), soil (soil moisture), tmmx (max temp)
 *   Terrain:  elevation (SRTM)
 *   Spectral means (growing-season, full period):
 *     NDWI, MNDWI, NDVI, NDMI, BSI
 *   Label:    ECI2025  (2025 Ecological Condition Index, 0..1)
 *
 * NOTE on interpretation: climate + terrain are INDEPENDENT drivers of
 * condition; the spectral means overlap with how ECI is built, so in the
 * SHAP plot I will separate "independent drivers" (climate/terrain) from
 * "state indices" - you can drop the spectral predictors if you want a
 * purely climatic attribution.
 **********************************************************************/

// ---- AOI (WDPA Ramsar, Turkey) -------------------------------------------
var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons');
var cand = wdpa.filter(ee.Filter.and(
    ee.Filter.stringContains('NAME', 'Sultan'), ee.Filter.eq('ISO3', 'TUR')));
var ramsar = cand.filter(ee.Filter.stringContains('DESIG_ENG', 'Ramsar'));
var aoi = ee.Geometry(ee.Algorithms.If(ramsar.size().gt(0),
            ramsar.geometry().dissolve(1), cand.geometry().dissolve(1)));
Map.centerObject(aoi, 11);
print('AOI area (km2):', aoi.area(1).divide(1e6));

var MS = 8, ME = 9, MAXC = 60;

// ---- Landsat indices (as before) -----------------------------------------
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
      .rename('BSI')]);
}
function pTM(i){return idx(ee.Image(maskL2(i).select(
  ['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B7'],
  ['blue','green','red','nir','swir1','swir2']).multiply(0.0000275).add(-0.2)));}
function pOLI(i){return idx(ee.Image(maskL2(i).select(
  ['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],
  ['blue','green','red','nir','swir1','swir2']).multiply(0.0000275).add(-0.2)));}
function coll(y0,y1){
  function b(id,p){return ee.ImageCollection(id).filterBounds(aoi)
    .filter(ee.Filter.calendarRange(y0,y1,'year'))
    .filter(ee.Filter.calendarRange(MS,ME,'month'))
    .filter(ee.Filter.lte('CLOUD_COVER_LAND',MAXC)).map(p);}
  return b('LANDSAT/LT04/C02/T1_L2',pTM).merge(b('LANDSAT/LT05/C02/T1_L2',pTM))
    .merge(b('LANDSAT/LE07/C02/T1_L2',pTM)).merge(b('LANDSAT/LC08/C02/T1_L2',pOLI))
    .merge(b('LANDSAT/LC09/C02/T1_L2',pOLI));
}
var specMean = coll(1984,2025).mean().rename(['NDVI','NDWI','MNDWI','NDMI','BSI']);

// ---- 2025 ECI label (same definition as the condition run) ---------------
function norm(x,lo,hi){return x.subtract(lo).divide(hi-lo).clamp(0,1);}
var ix25 = coll(2023,2025).median();
var wet = ee.Image.cat([norm(ix25.select('NDWI'),-0.4,0.5),
                        norm(ix25.select('MNDWI'),-0.4,0.6),
                        norm(ix25.select('NDMI'),-0.3,0.4)]).reduce(ee.Reducer.mean());
var eci25 = wet.multiply(0.60)
  .add(norm(ix25.select('NDVI'),0.1,0.6).multiply(0.25))
  .add(ee.Image(1).subtract(norm(ix25.select('BSI'),0.0,0.4)).multiply(0.15))
  .clamp(0,1).rename('ECI2025');

// ---- Climate (TerraClimate, growing-season mean, scaled to real units) ----
var tc = ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE')
  .filter(ee.Filter.calendarRange(1984,2025,'year'))
  .filter(ee.Filter.calendarRange(MS,ME,'month'));
var clim = ee.Image.cat([
  tc.select('pr').mean().rename('pr'),
  tc.select('pet').mean().multiply(0.1).rename('pet'),
  tc.select('def').mean().multiply(0.1).rename('def'),
  tc.select('soil').mean().multiply(0.1).rename('soil'),
  tc.select('tmmx').mean().multiply(0.1).rename('tmmx')
]);

// ---- Terrain --------------------------------------------------------------
var elev = ee.Image('USGS/SRTMGL1_003').rename('elevation');

// ---- Stack + export -------------------------------------------------------
var stack = clim.addBands(elev).addBands(specMean).addBands(eci25)
              .toFloat().clip(aoi);
print('bands', stack.bandNames());
Map.addLayer(eci25, {min:0.15,max:0.75,
  palette:['d62828','ef7d34','f4c430','7cb342','1a7a3f']}, 'ECI 2025', true);

Export.image.toDrive({
  image: stack,
  description:'SultanMarshes_driver_stack',
  folder:'GEE_SultanMarshes',
  fileNamePrefix:'sultan_driver_stack',
  region: aoi, scale: 30, crs:'EPSG:32636', maxPixels: 1e13
});
// Run -> start the export -> send sultan_driver_stack.tif back.
