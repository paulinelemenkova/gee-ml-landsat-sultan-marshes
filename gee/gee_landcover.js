/**********************************************************************
 * Sultan Marshes - wetland land-cover evolution for Figure 7 (rebuild)
 * Four epochs (1984, 2000, 2015, 2025) matching Table 3, clipped to the
 * wetland so class areas sum to ~176 km2 (not the ~1800 km2 full scene).
 *
 * Reproducible index-threshold classification into 7 classes:
 *   1 Open Water | 2 Seasonal Water | 3 Reed Bed/Marsh | 4 Wet Meadow
 *   5 Agriculture | 6 Bare Soil | 7 Other Land
 *
 * Exports (to Google Drive):
 *   (A) classified multiband GeoTIFF (one band per epoch) -> for the map panels
 *   (B) per-epoch per-class area CSV (km2)                -> for the area chart
 * Send both back and Figure 7 (maps + stacked area chart) will be rendered.
 **********************************************************************/

// ===== 1. WETLAND BOUNDARY (no upload needed - taken from WDPA) ===========
// The Sultan Marshes protected area is already in Earth Engine's World
// Database on Protected Areas, so no shapefile is required.
var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons');
var cand = wdpa.filter(ee.Filter.stringContains('NAME', 'Sultan'));
print('WDPA candidates (NAME, DESIG_ENG, REP_AREA km2):',
      cand.select(['NAME', 'DESIG_ENG', 'REP_AREA']));

// Prefer the Ramsar wetland (~172 km2); fall back to any 'Sultan' match.
var ramsar = cand.filter(ee.Filter.stringContains('DESIG_ENG', 'Ramsar'));
var aoi = ee.Geometry(ee.Algorithms.If(ramsar.size().gt(0),
            ramsar.geometry().dissolve(1),
            cand.geometry().dissolve(1)));

Map.centerObject(aoi, 11);
Map.addLayer(aoi, {color: 'red'}, 'Wetland boundary (WDPA)', false);
print('AOI area (km2) - expect ~150-250:', aoi.area(1).divide(1e6));

// If WDPA returns nothing or the wrong polygon: draw a polygon with the
// geometry tool, name it 'aoi', and delete the block above -- or ask me for
// the data-driven fixed-footprint fallback (maximum 1984 wetland extent).

// ===== 2. Epochs (match Table 3) ==========================================
var EPOCHS = [
  {label: '1984', y0: 1984, y1: 1986},
  {label: '2000', y0: 1998, y1: 2002},
  {label: '2015', y0: 2013, y1: 2017},
  {label: '2025', y0: 2023, y1: 2025}
];
var MONTH_START = 8, MONTH_END = 9, MAX_CLOUD = 60;

// ===== 3. Masking, scaling, indices (as in the trend script) ==============
function maskL2(img) {
  var qa = img.select('QA_PIXEL');
  var bad = qa.bitwiseAnd(1 << 1).neq(0).or(qa.bitwiseAnd(1 << 2).neq(0))
      .or(qa.bitwiseAnd(1 << 3).neq(0)).or(qa.bitwiseAnd(1 << 4).neq(0))
      .or(qa.bitwiseAnd(1 << 5).neq(0));
  return img.updateMask(bad.not()).updateMask(img.select('QA_RADSAT').eq(0));
}
function addIndices(sr) {
  var ndvi  = sr.normalizedDifference(['nir', 'red']).rename('NDVI');
  var ndwi  = sr.normalizedDifference(['green', 'nir']).rename('NDWI');
  var mndwi = sr.normalizedDifference(['green', 'swir1']).rename('MNDWI');
  var ndmi  = sr.normalizedDifference(['nir', 'swir1']).rename('NDMI');
  var bsi   = sr.expression('((S1+R)-(N+B))/((S1+R)+(N+B))',
      {S1: sr.select('swir1'), R: sr.select('red'),
       N: sr.select('nir'), B: sr.select('blue')}).rename('BSI');
  return ee.Image.cat([ndvi, ndwi, mndwi, ndmi, bsi])
           .copyProperties(sr, ['system:time_start']);
}
function prepTM(img) {
  return addIndices(ee.Image(maskL2(img)
      .select(['SR_B1','SR_B2','SR_B3','SR_B4','SR_B5','SR_B7'],
              ['blue','green','red','nir','swir1','swir2'])
      .multiply(0.0000275).add(-0.2)));
}
function prepOLI(img) {
  return addIndices(ee.Image(maskL2(img)
      .select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],
              ['blue','green','red','nir','swir1','swir2'])
      .multiply(0.0000275).add(-0.2)));
}
function epochComposite(y0, y1) {
  function b(id, prep) {
    return ee.ImageCollection(id).filterBounds(aoi)
      .filter(ee.Filter.calendarRange(y0, y1, 'year'))
      .filter(ee.Filter.calendarRange(MONTH_START, MONTH_END, 'month'))
      .filter(ee.Filter.lte('CLOUD_COVER_LAND', MAX_CLOUD)).map(prep);
  }
  return b('LANDSAT/LT04/C02/T1_L2', prepTM)
    .merge(b('LANDSAT/LT05/C02/T1_L2', prepTM))
    .merge(b('LANDSAT/LE07/C02/T1_L2', prepTM))
    .merge(b('LANDSAT/LC08/C02/T1_L2', prepOLI))
    .merge(b('LANDSAT/LC09/C02/T1_L2', prepOLI))
    .median();
}

// ===== 4. Index-threshold classification (7 classes) ======================
// Thresholds are adjustable; later where() calls take priority.
function classify(ix) {
  var w = ix.select('MNDWI'), nd = ix.select('NDVI'),
      ndmi = ix.select('NDMI'), bsi = ix.select('BSI');
  var c = ee.Image(7).rename('class');                 // 7 Other Land (default)
  c = c.where(bsi.gt(0.10).and(nd.lt(0.20)), 6);        // 6 Bare Soil
  c = c.where(nd.gt(0.35).and(w.lt(-0.20)), 5);         // 5 Agriculture (green, dry)
  c = c.where(nd.gt(0.15).and(nd.lte(0.35))
              .and(ndmi.gt(0.0)).and(w.lt(0.0)), 4);    // 4 Wet Meadow
  c = c.where(nd.gt(0.30).and(w.gte(-0.10)), 3);        // 3 Reed Bed / Marsh
  c = c.where(w.gt(0.00).and(w.lte(0.20)), 2);          // 2 Seasonal Water
  c = c.where(w.gt(0.20), 1);                           // 1 Open Water (priority)
  return c.updateMask(ix.select('NDVI').mask()).toByte();
}

// ===== 5. Classify each epoch + collect areas =============================
var PALETTE = ['08519c','6baed6','238b45','a1d99b','fed976','b8935f','969696'];
var CLASS_NAMES = ['Open Water','Seasonal Water','Reed Bed/Marsh','Wet Meadow',
                   'Agriculture','Bare Soil','Other Land'];

var classifiedBands = [];
var areaFeatures = [];
EPOCHS.forEach(function (e) {
  var ix = epochComposite(e.y0, e.y1);
  var cls = classify(ix).clip(aoi).rename('cls_' + e.label);
  classifiedBands.push(cls);

  // per-class area (km2) within the wetland
  var areaImg = ee.Image.pixelArea().divide(1e6)
      .addBands(cls.rename('class'));
  var grouped = ee.List(areaImg.reduceRegion({
    reducer: ee.Reducer.sum().group({groupField: 1, groupName: 'class'}),
    geometry: aoi, scale: 30, maxPixels: 1e13
  }).get('groups'));
  grouped.evaluate(function (list) {
    print(e.label + ' class areas (km2):', list);
  });
  // write one CSV row per class
  for (var k = 1; k <= 7; k++) {
    var km2 = ee.Number(ee.Dictionary(
        ee.List(grouped).filter(ee.Filter.eq('class', k)).get(0)
        ).get('sum', 0));    // 0 if class absent
    areaFeatures.push(ee.Feature(null,
        {epoch: e.label, class_id: k, class_name: CLASS_NAMES[k - 1], area_km2: km2}));
  }
  Map.addLayer(cls, {min: 1, max: 7, palette: PALETTE}, 'Classes ' + e.label,
               e.label === '2025');
});

var classified = ee.Image.cat(classifiedBands);        // 4 bands (one per epoch)
var areaTable = ee.FeatureCollection(areaFeatures);
print('Area table (send this CSV back)', areaTable);

// ===== 6. Exports =========================================================
Export.image.toDrive({
  image: classified.toByte(),
  description: 'SultanMarshes_landcover_epochs',
  folder: 'GEE_SultanMarshes',
  fileNamePrefix: 'sultan_landcover_4epochs',
  region: aoi, scale: 30, crs: 'EPSG:32636', maxPixels: 1e13
});
Export.table.toDrive({
  collection: areaTable,
  description: 'SultanMarshes_class_areas',
  folder: 'GEE_SultanMarshes',
  fileNamePrefix: 'sultan_class_areas',
  fileFormat: 'CSV',
  selectors: ['epoch', 'class_id', 'class_name', 'area_km2']
});
// Run the script, then start BOTH tasks in the Tasks tab.
