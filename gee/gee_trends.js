/**********************************************************************
 * Sultan Marshes - per-pixel trend rasters for Figure 5
 * Theil-Sen slope + Mann-Kendall (tau, p-value) of five spectral indices
 * NDWI, MNDWI, NDVI, NDMI, BSI  over the growing season 1984-2025.
 *
 * Data: Landsat Collection 2, Level-2 surface reflectance (WRS-2 176/033).
 * Run in the Earth Engine Code Editor: https://code.earthengine.google.com
 * Output: one multiband GeoTIFF exported to Google Drive -> send it back
 *         so it can be plotted as Figure 5.
 *
 * Bands exported (per index): <IDX>_slope, <IDX>_tau, <IDX>_p
 *   slope = index change per year (same units as Table 2, yr^-1)
 *   tau   = Mann-Kendall / Kendall rank correlation with time
 *   p     = two-sided significance (map stipple where p < 0.05)
 **********************************************************************/

// ---- 1. Area of interest ------------------------------------------------
// Default: the Develi basin window (matches the study-area map, Figure 2).
var aoi = ee.Geometry.Rectangle([34.83, 38.00, 35.55, 38.72]);

// To clip to the National Park / Ramsar boundary instead, upload it as an
// asset and uncomment (replace the path with your asset id):
// var aoi = ee.FeatureCollection('users/YOUR_USERNAME/sultan_marshes_boundary').geometry();

Map.centerObject(aoi, 10);
Map.addLayer(aoi, {color: 'black'}, 'AOI', false);

// ---- 2. Parameters ------------------------------------------------------
var START_YEAR = 1984;
var END_YEAR   = 2025;
var MONTH_START = 8;      // growing-season window: 1 Aug ...
var MONTH_END   = 9;      // ... 30 Sep  (keep constant every year)
var MAX_CLOUD   = 60;     // scene-level land cloud cover (%); median handles the rest
var USE_L7_SLCOFF = true; // set false to drop Landsat 7 after 2003 (striping)

// ---- 3. QA_PIXEL cloud / shadow / snow mask (Fmask, C2 L2) --------------
function maskL2(img) {
  var qa  = img.select('QA_PIXEL');
  var bad = qa.bitwiseAnd(1 << 1).neq(0)   // dilated cloud
      .or(qa.bitwiseAnd(1 << 2).neq(0))    // cirrus (OLI)
      .or(qa.bitwiseAnd(1 << 3).neq(0))    // cloud
      .or(qa.bitwiseAnd(1 << 4).neq(0))    // cloud shadow
      .or(qa.bitwiseAnd(1 << 5).neq(0));   // snow
  var sat = img.select('QA_RADSAT').eq(0); // no band saturation
  return img.updateMask(bad.not()).updateMask(sat);
}

// ---- 4. Scale factors, band harmonisation, indices ---------------------
function addIndices(sr) {
  var ndvi  = sr.normalizedDifference(['nir', 'red']).rename('NDVI');
  var ndwi  = sr.normalizedDifference(['green', 'nir']).rename('NDWI');
  var mndwi = sr.normalizedDifference(['green', 'swir1']).rename('MNDWI');
  var ndmi  = sr.normalizedDifference(['nir', 'swir1']).rename('NDMI');
  var bsi   = sr.expression(
      '((S1 + R) - (N + B)) / ((S1 + R) + (N + B))',
      {S1: sr.select('swir1'), R: sr.select('red'),
       N: sr.select('nir'),  B: sr.select('blue')}).rename('BSI');
  return ee.Image.cat([ndvi, ndwi, mndwi, ndmi, bsi])
           .copyProperties(sr, ['system:time_start']);
}
function prepTM(img) {   // Landsat 4/5/7 : SR_B1,2,3,4,5,7
  var sr = maskL2(img)
      .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B7'],
              ['blue','green','red','nir','swir1','swir2'])
      .multiply(0.0000275).add(-0.2)
      .copyProperties(img, ['system:time_start']);
  return addIndices(ee.Image(sr));
}
function prepOLI(img) {  // Landsat 8/9 : SR_B2,3,4,5,6,7
  var sr = maskL2(img)
      .select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],
              ['blue','green','red','nir','swir1','swir2'])
      .multiply(0.0000275).add(-0.2)
      .copyProperties(img, ['system:time_start']);
  return addIndices(ee.Image(sr));
}

// ---- 5. Build and merge the sensors ------------------------------------
function build(id, prep) {
  var c = ee.ImageCollection(id)
      .filterBounds(aoi)
      .filter(ee.Filter.calendarRange(START_YEAR, END_YEAR, 'year'))
      .filter(ee.Filter.calendarRange(MONTH_START, MONTH_END, 'month'))
      .filter(ee.Filter.lte('CLOUD_COVER_LAND', MAX_CLOUD));
  return c.map(prep);
}
var l7 = build('LANDSAT/LE07/C02/T1_L2', prepTM);
if (!USE_L7_SLCOFF) {
  l7 = l7.filter(ee.Filter.lt('system:time_start',
                 ee.Date('2003-06-01').millis()));
}
var all = build('LANDSAT/LT04/C02/T1_L2', prepTM)
    .merge(build('LANDSAT/LT05/C02/T1_L2', prepTM))
    .merge(l7)
    .merge(build('LANDSAT/LC08/C02/T1_L2', prepOLI))
    .merge(build('LANDSAT/LC09/C02/T1_L2', prepOLI));

print('Total clear scenes used:', all.size());

// ---- 6. Annual growing-season median composites ------------------------
var years = ee.List.sequence(START_YEAR, END_YEAR);
var annual = ee.ImageCollection(years.map(function (y) {
  y = ee.Number(y);
  var comp = all.filter(ee.Filter.calendarRange(y, y, 'year')).median();
  var t = ee.Image.constant(y).float().rename('t');
  return comp.addBands(t)
             .set('year', y)
             .set('system:time_start', ee.Date.fromYMD(y, 1, 1).millis());
}));

// QC: number of scenes contributing to each year (check none are 0)
print('Scenes per year', ee.FeatureCollection(years.map(function (y) {
  y = ee.Number(y);
  return ee.Feature(null, {year: y,
      n: all.filter(ee.Filter.calendarRange(y, y, 'year')).size()});
})));

// ---- 7. Per-pixel Theil-Sen slope + Mann-Kendall ------------------------
var INDICES = ['NDWI', 'MNDWI', 'NDVI', 'NDMI', 'BSI'];

function trend(idx) {
  // 2-band series [t, index]; mask t where the index is masked
  var tcoll = annual.map(function (img) {
    var v = img.select(idx);
    return img.select('t').updateMask(v.mask()).addBands(v);   // order: t, idx
  });
  var sen = tcoll.reduce(ee.Reducer.sensSlope());              // slope, offset
  var mk  = tcoll.reduce(ee.Reducer.kendallsCorrelation(2));   // tau, p-value
  return sen.select('slope').rename(idx + '_slope')
      .addBands(mk.select(0).rename(idx + '_tau'))
      .addBands(mk.select(1).rename(idx + '_p'));
}

var trends = ee.Image.cat(INDICES.map(trend)).clip(aoi).toFloat();
print('Output bands', trends.bandNames());

// ---- 8. Quick-look layers (drying = red, wetting = blue) ---------------
var divPal = ['#b2182b', '#ef8a62', '#fddbc7', '#f7f7f7',
              '#d1e5f0', '#67a9cf', '#2166ac'];
Map.addLayer(trends.select('NDWI_slope'),
  {min: -0.012, max: 0.012, palette: divPal}, 'NDWI Sen slope');
Map.addLayer(trends.select('MNDWI_slope'),
  {min: -0.012, max: 0.012, palette: divPal}, 'MNDWI Sen slope', false);
Map.addLayer(trends.select('NDWI_p').lte(0.05).selfMask(),
  {palette: ['black']}, 'NDWI significant (p<0.05)', false);

// ---- 9. Export the multiband trend raster to Drive ---------------------
Export.image.toDrive({
  image: trends,
  description: 'SultanMarshes_trends_1984_2025',
  folder: 'GEE_SultanMarshes',
  fileNamePrefix: 'sultan_trends_slope_MK',
  region: aoi,
  scale: 30,
  crs: 'EPSG:32636',           // UTM Zone 36N, matches the manuscript
  maxPixels: 1e13
});
// After running: open the "Tasks" tab (top-right) and click "Run" to start
// the export, then download sultan_trends_slope_MK.tif from Google Drive.
