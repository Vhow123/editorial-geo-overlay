# Editorial geo overlay

## What this skill is

- Turn a travel photo into an editorial geo visual: the original photo is never regenerated, a real map is composited over sky, sea or other negative space, and a red dot marks the shooting point.
- The default map is a real road network, not a decorative pattern. See Failure review, 2026-10-23 below: schematic contours were the mistake that made two whole versions wrong.
- Place names, coordinates, altitude and direction are used only when they were actually verified. Everything else is left out, not guessed.

## Failure review, 2026-10-23 (Bijie sunrise photo)

The user said the first version had not changed, then sent another person's Xi'an photo and asked whether the difference was not obvious. It was obvious, and these were the causes. Do not repeat them:

1. Never looked at the reference style first. The Xi'an reference is: a large serif city name and coordinates top left, a compass rose and a 0-1-2-4 km scale bar on the left, a real city street network filling the sky, a red dot on a named landmark, and a few verified place labels. No contours, no square map card, no bounding box. The first versions matched none of that.
2. Invented geometry and called it a map. The old helper drew random, seeded, wobbly contour rings. There was no contour data behind them, and no road data either. A decorative ring is not a geographic map, however thin and elegant it looks.
3. Treated user feedback as a contrast problem only. The real complaint was a different kind of map altogether. When feedback says the result is unchanged, stop and check what reference or expectation was missed before polishing the wrong thing.
4. Put text on a light cloud band. The first footer sat at about y = 0.31 on pale sky and was unreadable. Text must go in the dark part of the sky, or it must carry a dark stroke; moving it after delivery is not a fix, it is rework the user should never see.
5. Delivered the transparent layer as if it were a picture. White lines on a transparent background look blank when opened alone. That alone made the user think nothing had changed. The layer is a working file, never a deliverable (see Deliver only the main image).
6. Gave up on real data too easily. The first all-highways Overpass query timed out and a later one returned 502. The correct response is tiered queries and retries (see below), not falling back to invented contours.

## Failure review, 2026-10-29 (village photo set)

A first delivery for a village photo set had to be remade after two user corrections. Do not repeat these causes:

1. Used a city scale for a village. The first map was about 18 km wide, so the whole village shrank to a point and its lanes could not be read. A village needs a village scale, not the city default.
2. Drew carriageways only. The first map left out the stone paths and footpaths that are the main circulation inside a village, so the settlement looked empty even where the roads were real.
3. Left a white dot unexplained and labelled in pinyin only. The user had to ask what the white dot label meant. Every dot needs a Chinese legend and a Chinese label before delivery.
4. Delivered a map with no buildings and said nothing about it. Building footprint data was empty at the shooting centre, but the first delivery did not disclose that gap, so the user asked why the houses in the photo were missing from the map. Disclose an empty building centre in the first delivery and offer the two choices in Step 3. Never invent houses to fill the gap.

## Step 0: Read the reference first

- If the user sent, linked or described a reference image, analyse it before drawing anything, and list its elements in your working notes: title style and position, coordinate format, compass, scale bar, what the map lines actually are (roads, rivers, contours, trails), how dense they are, what the red dot marks, which labels exist, where the map sits, and how its edges fade.
- Match those elements. Do not substitute a different map style because it is easier to draw. If the reference is a road map, draw roads. If it is a trail map, draw trails from a real source.
- If there is no reference, use the Xi'an-style layout in Layout below as the default: real roads, serif title, compass, scale bar.
- If the user asked for contours explicitly, say plainly that the contours are schematic and not to scale, and only use them when the user explicitly accepts that after the real-map option has been offered.

## Step 1: Read the photo location first

- Start from the original file the user sent, not from a chat preview or a resized copy.
- Read the EXIF with muse.exec and Python Pillow before you draw anything.
- Use getexif plus get_ifd for the GPS block, and convert degrees minutes seconds to decimal degrees yourself.
- Record the latitude, longitude, altitude, camera direction, shooting time and device only if the EXIF actually contains them.
- Treat a blank location field in the user message as no information, never as proof that the photo has no GPS.
- If the first EXIF read shows no GPS block, say so plainly and stop inventing a place name.
- If you once told the user there was no precise location and a later check finds GPS, correct that statement in the same conversation.

## Step 2: Verify every place name before labelling

- Reverse geocode the verified GPS point with browser.browse on OpenStreetMap Nominatim, and keep the exact hierarchy it returns.
- Keep the road, village, county, city and province exactly as returned, and do not fill in a missing level such as township.
- Record a nearest named place only with the distance and direction that the lookup supports, and keep different village names from different entries separate. A distance you calculated from two coordinates must be labelled as calculated, not as a Nominatim field.
- Do not claim a mountain range, a named peak, a wind farm, a trail name or a scenic spot name when the lookup returns nothing for it.
- Keep the altitude and direction from EXIF separate from map labels, and say which source each number came from when you present the result.
- When there is no GPS at all, mark only an approximate area, write that the topography is schematic and not to scale, and add no coordinates.

## Step 3: Fetch a real road network (Overpass, not invented lines)

- Centre the map bbox on the verified shooting point. Size it from the settlement type, not from a fixed city default. For a city photo use roughly 15 to 20 km wide. For a village, a historic settlement, or a single scenic cluster use about 4 km wide, with a 2 km scale bar. Then set the latitude span so the geographic aspect matches the pixel aspect of the map rectangle (see the helper's scale calculation). Bijie example that worked: lon span 0.18 degrees (about 17.8 km), lat span 0.0694 degrees (about 7.7 km), for a 1228 by 528 px map zone.
- Query Overpass in three tiers, in this order, and save the raw JSON beside the output for audit. These are working files, not deliverables: Major way highway motorway trunk primary secondary tertiary, Minor way highway unclassified residential road living_street, Footpaths way highway footway path pedestrian steps, each with south west north east and out geom.
- The helper has no footpath input. Save the footpath JSON separately for audit, then build one merged minor file whose elements are the minor elements plus the footpath elements, and pass that merged file as --osm-minor. The helper draws every way in --osm-minor thin and faint, so merged footpaths stay readable without overtaking major roads. Do not pass a third Overpass file to the helper, because it has no argument for it.
- Overpass is flaky: a 502 or a timeout is not proof that the roads do not exist. Retry the same tiered query up to four times, with a few seconds between attempts, before concluding anything.
- If Overpass still fails after those retries, and especially if it returns 406 or 403, do not keep retrying it. That block was observed from this machine on 2026-10-29, with the main endpoint returning 406 and the French mirror returning 403, and the next build used the fallback below instead of stalling.
- For a small bbox, fetch the same bbox from the OSM main API map call at https://api.openstreetmap.org/api/0.6/map?bbox=west,south,east,north and use the full OSM XML it returns for that bbox. This is the fallback that supplied the road network for the 2026-10-29 Xijiang photo when Overpass was blocked.
- Convert that XML locally into the Overpass JSON like format the builder expects, grouping ways into major, minor and foot tiers by their highway value, and keep full geometry for ways that cross the bbox edge. Feed the converted tiers into the same merged minor and major files as an Overpass result, then continue the build unchanged. Do not present this fallback as a general replacement for Overpass on a large city bbox, because the working evidence covers a small bbox only.
- If real road data cannot be fetched after those retries and the fallback above, say so plainly. Do not fall back to random contours and call the result a map. Offer a schematic version only if the user explicitly accepts it, labelled schematic and not to scale.
- Before the first delivery, check building footprint coverage around the shooting point with a small bbox query for building footprints. If the centre is empty, say so in the first delivery, say you will not invent houses, and offer two choices: switch to a source with building data, or use hand drawn schematic houses labelled schematic and not to scale. A map with no buildings is acceptable only when that gap is disclosed before the user has to ask.
- Building sources that actually cover China (verified 2026-10-29 for Xijiang): Microsoft footprints exclude China and Google Open Buildings covers only the Global South, so neither helps. GBA's ODbL tile (HuggingFace zhu-xlab/GBA.ODbLPolygon, 5 degree by 5 degree tiles) is OSM plus Microsoft only and was 0 buildings inside the Xijiang 4 km box. CLSM (Shi et al. 2024, 280M buildings in East Asia, Zenodo doi:10.5281/zenodo.8174931, one Shapefile per prefecture) had 396 buildings inside the same box and is the source that fixed the Xijiang map. Two coordinate traps: CLSM .shp files are in UTM metres (Guizhou is zone 49N), and GBA ODbL GeoJSON coordinates are EPSG:3857 metres; neither is lon/lat, and treating them as degrees yields a false zero. Use pyproj, never a hand rolled inverse projection, for the conversion. The full GBA.Polygon on mediaTUM was rate limited (429) when tried; prefer the CLSM direct download, fetched by HTTP range request on the single 23 GB zip (read the ZIP64 central directory, then pull only the prefecture's .shp/.shx/.dbf/.prj/.cpg entries). CLSM imagery is 2020-2022 vintage with reported 89.63 percent overall accuracy and 82.55 percent F1, so disclose that individual outlines may differ from the current scene.
- Draw minor roads first (thin, faint), then major roads on top. In the working Bijie version: minor width 1, alpha about 110; motorway, trunk and primary width 2, alpha 205 to 225; secondary width 2, alpha about 185; tertiary width 1 to 2, alpha about 165. All in low-saturation off-white (238, 238, 232). No other road colours, no invented roads.

## Step 3b: Building layer (v5 logic, standing rule since 2026-10-29)

This is the standing procedure for the building question, set by the user after the Xijiang v5 rebuild: check coverage first, rebuild with real footprints when found, stop when not found. Never fabricate houses, and never present hand drawn houses as surveyed data.

1. Check in this order, and count in the actual map bbox. Overpass building query first (Xijiang: 29 in the 18x8 km box, 0 at the centre). Then the GBA ODbL tile, which is OSM plus Microsoft only and is not the full GBA product (Xijiang: 0 in the 4 km box). Then CLSM direct (below). For every source, report the count inside the map bbox and the count within 100 m and 500 m of each viewpoint, not just the dataset name. A source counts as usable only when it has buildings at the shooting centre, not merely somewhere in the wider area.
2. CLSM fetch (the source that fixed Xijiang). Shi et al. 2024, 280M buildings in East Asia, Zenodo doi:10.5281/zenodo.8174931, one Shapefile per prefecture (Xijiang is in the Qiandongnan file). Do not download the whole 23 GB zip: read the last 2 MB for the ZIP64 end of central directory, follow the ZIP64 locator to the real central directory offset, parse it, and range-download only that prefecture's .shp/.shx/.dbf/.prj/.cpg entries (about 32 MB compressed for Qiandongnan). Convert coordinates with pyproj only: CLSM .shp files are UTM metres (Guizhou is EPSG:32649), GBA ODbL GeoJSON coordinates are EPSG:3857 metres; neither is lon/lat, and treating either as degrees yields a false zero. A hand rolled inverse Transverse Mercator was tried and was 72 m off in latitude; do not hand roll it again.
3. Decide by the count. If the centre has usable buildings, rebuild with them (step 4). If every source is 0 at the centre, stop, report the counts and the sources tried, and offer the hand drawn schematic option labelled schematic and not to scale. Do not rebuild a version that still has no buildings and hope the user will not notice.
4. Draw buildings as a real layer, not as decoration. Use scripts/make_v5.py with --buildings pointing at a JSON file of polygons already converted to lon/lat rings. Draw buildings on the roads layer BEFORE the edge fade, buildings first, then footpaths, minor roads and major roads over them, so roads stay visible across blocks. Style: same off-white ink (238, 238, 232), fill alpha 150, outline alpha 220 width 1. Skip rings entirely outside the map bbox. Use --portrait for portrait photos: it switches the title to size 54 with the portrait coords/subline layout; landscape keeps title size 42. Keep every other element, config value and road file exactly as the previous delivered version.
5. Verify the pipeline before changing anything. Rebuild one photo with the new script but WITHOUT buildings and WITHOUT the legend, and diff it against the previously delivered file. The Xijiang check caught a real trap this way: the delivered 4 km version was the *_zoom.jpg files, not the *_geo.jpg mains (the mains were the old 18 km version with a 4 km scale bar). A diff confined to the legend area plus JPEG edge noise confirms the pipeline; a road-shaped diff means the wrong inputs. Only then build the full set with buildings.
6. Chinese labels and legend are part of the build, not an extra. Nearby place labels are Chinese, never pinyin alone (Xijiang: Dongyin became the Chinese name for Dongyin viewing platform). The legend is drawn on the layer after the fade, inside the map zone, with a red dot sample for the shooting point and a white dot sample for a nearby landmark, each with its Chinese meaning. Place it at the bottom of the map zone on the side opposite the scale bar: left side when the scale bar is centred or right, right side when the scale bar is left, so it never collides with the scale ticks. Use NotoSerifCJK-Bold.ttc index 2 (SC) for Chinese text; DejaVu has no Chinese glyphs.
7. Keep the numbers ready, but do not put them in the delivery message. Record the source, the bbox count and the 100 m and 500 m counts per photo, and the vintage and accuracy, in working notes, and give them only when the user asks for details. The delivery message itself follows Deliver only the main image below: the image plus one short line, plus a second short sentence only when a warning applies, for example no buildings were found or a layer is schematic. Name the files as a new version (Xijiang: *_v5_geo.jpg) and leave the previous delivered files untouched.
- Draw footpaths thin and faint, so village lanes and stone paths stay readable without overtaking major roads. In a village, footpaths are the main circulation, not decoration, and leaving them out makes the settlement look empty. Reach this through the merged minor file above, because the helper has no separate footpath style.
- Project each way's geometry with a linear lon/lat projection into the map rectangle. A nearby place label must be placed at its own projected coordinates, never hand-placed in a convenient direction.
- A sparse road network in a suburban or mountain-edge photo is a real result, not a drawing failure. Do not densify it by hand. Say so when you deliver, as was done for Bijie versus Xi'an's inner-city grid.

## Layout (Xi'an reference layout, the default)

- Map zone: sky, sea or other negative space, roughly the top third of the frame (Bijie: left 0.04, right 0.97, top 0.03, bottom 0.33 as fractions of width and height). No square map card, no bounding box.
- Edge fade: fade the road layer out over about 70 px inside the map rectangle, with a smoothstep, so the map dissolves into the photo. Labels, title, compass and scale bar are drawn after the fade, so they stay readable.
- Title: serif capitals, letter-spaced, top left of the map zone (DejaVuSerif-Bold). Bijie: B I J I E.
- Coordinates below the title, to two decimal places, in the reference format, for example 27.28 degrees N and 105.30 degrees E. A smaller second line carries altitude and direction only when EXIF verified them, for example 1766 m and 62 degrees NE.
- Compass rose on the left, over the map: a thin circle, a four-point star, and N, E, S, W in serif. Not a small north arrow alone.
- Scale bar below the compass: ticks at 0, 1, 2 and the full scale. Use 4 km for a city map and 2 km for a village map. Compute pixels per kilometre from the map width: px_per_km = map_width_px / map_width_km, where map_width_km = lon_span * 111.32 * cos(mean_latitude). Do not copy another photo's pixel length.
- Shooting point: one red dot (193, 39, 45) with a white ring, at the projected EXIF point, with its verified place label next to it (Bijie: Biyang). A verified nearby place gets a small white dot at its projected coordinates and a short label (Bijie: Caodi, about 1.5 km south-east, calculated from coordinates).
- Add a short Chinese legend inside the map zone that explains every dot, for example red dot means shooting point and white dot means nearby landmark. Label a nearby place in Chinese, never in pinyin alone, and do not repeat the legend in the delivery text, because the image already carries it and the delivery rule below allows only one short line plus a warning sentence when needed. The helper does not draw a legend and has no legend config key, so add the legend in the post-processing step in Build with the helper, not in the config.
- Keep the number of labels small: city, shooting-point place, and at most one or two verified nearby places. Every label gets a thin dark stroke where a road line could cross it.
- Add only a very light paper grain, about 3 percent, so the print texture does not change the original colour or light.
- Keep the original width, height and aspect ratio unchanged, and keep the map off the main subject, the foreground and the horizon light that makes the photo work.

## Build with the helper

- Call the helper at ~/workspace/custom-skills/editorial_geo_overlay/scripts/make_editorial_geo.py with a config file that lists only verified values: geo bbox, map rectangle, title, coordinates, subline, viewpoint lon/lat/label, nearby places with lon/lat/label, and scale kilometres. See references/example-config.json for the current format.
- Do not hardcode one photo location into the helper. The helper takes the bbox, the config, and exactly two road files as arguments, --osm-major and --osm-minor, and it writes only the finished picture. Pass the merged minor file described in Step 3 as --osm-minor. Do not put a legend entry in the config, because the helper has no legend key and would not draw it.
- For any build that needs buildings, footpaths, a portrait layout or a legend, use scripts/make_v5.py instead: it takes the same config plus --osm-foot, --buildings (lon/lat polygon JSON, see Step 3b) and --portrait, and it draws the Chinese legend itself (see Step 3b step 6). Do not reimplement its legend in post-processing.
- If you use the older helper, add the Chinese legend by post-processing before you inspect or deliver. Open the helper output with Python Pillow, draw the legend inside the map zone in a dark area that does not cover the title, compass, scale bar, dots or labels, using a font on this machine that renders Chinese, and save that post-processed picture as the final picture. Include only the dot types actually present, with a red dot sample for the shooting point and a white dot sample for a nearby landmark, each with its Chinese meaning. If the Chinese characters do not render readably, fix the font and rebuild before delivery.
- The old contour helper is retired. Do not call it, do not copy its random-ring code, and do not present its output as a geographic map.

## Inspect the result and deliver

- Open the finished picture with muse.read and look at it before you send it.
- Inspect the post-processed final picture, not the helper output from before the legend was added.
- Check, in this order: is this a real road map or a pattern? Is the title, compass and scale bar readable? Is any label crossed by a road line in a way that breaks reading? Does any map line cover the main subject? Do the roads fade at the edges with no box?
- Check the village fixes before delivery: is the scale right for the settlement type, are village footpaths visible, does the Chinese legend explain every dot, and is an empty building centre disclosed with the two choices from Step 3?
- Check the building layer before delivery: are real building blocks visible around the red dot (not just roads), does the cluster match the settlement in the photo, and does no building polygon cover the main subject outside the map zone?
- Move a label into the dark part of the sky, thin a road class, or shrink the map zone when a check fails, then rebuild and look again. Do not deliver a version you have not looked at.
- Check that the mountains, buildings, sky and foreground are still the original photo, apart from the overlay area and the light grain.

## Deliver only the main image

- Reply with the picture directly and keep the text minimal: the attachment is the message. No long report before or after it, no retelling of the verification steps, counts, sources or caveats. One short line naming the picture is enough; add a second short sentence only when something in the picture itself needs a warning (for example, no buildings were found, or a layer is schematic). Full details go out only when the user asks for them. This is a standing user rule since 2026-10-29: do not pad a geo delivery with paragraphs.
- Deliver the finished picture as an attachment in the same message that announces it, and deliver nothing else as a picture.
- Do NOT attach, link or offer as a deliverable: the transparent map layer, a dark-background preview of the layer, the Overpass JSON files, or the build script. Those are working files. Keep them beside the output for later adjustment, but do not output them.
- If the user explicitly asks for the layer later, provide it then, with a note that white lines on transparency look blank on a light background. Until then, silence about the layer is correct.
- Give the plain words account of what came from EXIF, what came from the map lookup, what came from the real road data, what is schematic (if anything), and what you did not verify, only when the user asks for details. The delivery message itself stays minimal under the first bullet above.
- If building footprints are empty at the centre, state that in the delivery message as the one warning sentence allowed above, before the user has to notice the missing houses, and offer the two choices from Step 3.

## Available connectors

- [Places](/opt/hatch/connectors/places/CONNECTOR.md) for place details that can help identify a venue in a photo.
- Use muse.connector_search to find other connectors and muse.skill_search to find related skills.
- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- OpenStreetMap is good for reverse geocoding a GPS point and for checking the nearest peak, scenic area and road.
- OpenStreetMap Overpass API is the source for the real road network in Step 3. Carry the exact latitude and longitude into the query, ask for geometry, and retry on 502 or timeout before giving up.
- If Overpass stays blocked after retries, use the OSM main API map call for a small bbox as in Step 3, and carry the same bbox into that call.
- Carry the exact latitude and longitude into the browser.browse task for Nominatim, ask for the full hierarchy and the nearest named features, and ask the browser to report what it did not find as well as what it found.

## Alternatives for better results

- When a village map at city scale looks empty, enlarge to village scale and add footpaths before redrawing any other element.
- When building data is empty at the centre, offer a different building source or a labelled schematic instead of inventing footprints.
- When a nearby landmark name would only make sense in pinyin, use its Chinese name and explain it in the legend.
