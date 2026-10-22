# Editorial geo overlay

## What this skill is

- Turn a travel photo into an editorial geo visual: the original photo is
  never regenerated, a real map is composited over sky, sea or other
  negative space, and a red dot marks the shooting point.
- The default map is a real road network, not a decorative pattern.
  See "Failure review, 2026-10-23" below: schematic contours were the
  mistake that made two whole versions wrong.
- Place names, coordinates, altitude and direction are used only when
  they were actually verified. Everything else is left out, not guessed.

## Failure review, 2026-10-23 (Bijie sunrise photo)

The user said "做成地理图", then "不还是没变化", then sent another
person's Xi'an photo and asked whether the difference was not obvious.
It was obvious, and these were the causes. Do not repeat them:

1. **Never looked at the reference style first.** The Xi'an reference
   is: a large serif city name and coordinates top left, a compass rose
   and a 0-1-2-4 km scale bar on the left, a real city street network
   filling the sky, a red dot on a named landmark, and a few verified
   place labels. No contours, no square map card, no bounding box.
   The first versions matched none of that.
2. **Invented geometry and called it a map.** The old helper drew
   random, seeded, wobbly contour rings. There was no contour data
   behind them, and no road data either. A decorative ring is not a
   geographic map, however thin and elegant it looks.
3. **Treated user feedback as a contrast problem only.** "还是没变化"
   was answered by making the contours bolder and larger. The real
   complaint was a different kind of map altogether. When feedback
   says the result is unchanged, stop and check what reference or
   expectation was missed before polishing the wrong thing.
4. **Put text on a light cloud band.** The first footer sat at about
   y = 0.31 on pale sky and was unreadable. Text must go in the dark
   part of the sky, or it must carry a dark stroke; moving it after
   delivery is not a fix, it is rework the user should never see.
5. **Delivered the transparent layer as if it were a picture.** White
   lines on a transparent background look blank when opened alone.
   That alone made the user think nothing had changed. The layer is a
   working file, never a deliverable (see "Deliver only the main image").
6. **Gave up on real data too easily.** The first all-highways
   Overpass query timed out and a later one returned 502. The correct
   response is tiered queries and retries (see below), not falling
   back to invented contours.

## Step 0: Read the reference first

- If the user sent, linked or described a reference image, analyse it
  before drawing anything, and list its elements in your working notes:
  title style and position, coordinate format, compass, scale bar,
  what the map lines actually are (roads, rivers, contours, trails),
  how dense they are, what the red dot marks, which labels exist,
  where the map sits, and how its edges fade.
- Match those elements. Do not substitute a different map style
  because it is easier to draw. If the reference is a road map, draw
  roads. If it is a trail map, draw trails from a real source.
- If there is no reference, use the Xi'an-style layout in "Layout"
  below as the default: real roads, serif title, compass, scale bar.
- If the user asked for contours explicitly, say plainly that the
  contours are schematic and not to scale, and only use them when
  the user explicitly accepts that after the real-map option has
  been offered.

## Step 1: Read the photo location first

- Start from the original file the user sent, not from a chat preview
  or a resized copy.
- Read the EXIF with `muse.exec` and Python Pillow before you draw
  anything.
- Use `getexif` plus `get_ifd` for the GPS block, and convert degrees
  minutes seconds to decimal degrees yourself.
- Record the latitude, longitude, altitude, camera direction, shooting
  time and device only if the EXIF actually contains them.
- Treat a blank location field in the user message as no information,
  never as proof that the photo has no GPS.
- If the first EXIF read shows no GPS block, say so plainly and stop
  inventing a place name.
- If you once told the user there was no precise location and a later
  check finds GPS, correct that statement in the same conversation.

## Step 2: Verify every place name before labelling

- Reverse geocode the verified GPS point with `browser.browse` on
  OpenStreetMap Nominatim, and keep the exact hierarchy it returns.
- Keep the road, village, county, city and province exactly as
  returned, and do not fill in a missing level such as township.
- Record a nearest named place only with the distance and direction
  that the lookup supports, and keep different village names from
  different entries separate. A distance you calculated from two
  coordinates must be labelled as calculated, not as a Nominatim field.
- Do not claim a mountain range, a named peak, a wind farm, a trail
  name or a scenic spot name when the lookup returns nothing for it.
- Keep the altitude and direction from EXIF separate from map labels,
  and say which source each number came from when you present the
  result.
- When there is no GPS at all, mark only an approximate area, write
  that the topography is schematic and not to scale, and add no
  coordinates.

## Step 3: Fetch a real road network (Overpass, not invented lines)

- Centre the map bbox on the verified shooting point. Size it from
  the photo's map rectangle, not from a guess: pick the longitude span
  so the map width is roughly 15 to 20 km for a city photo, then set
  the latitude span so the geographic aspect matches the pixel aspect
  of the map rectangle (see the helper's scale calculation).
  Bijie example that worked: lon span 0.18 degrees (about 17.8 km),
  lat span 0.0694 degrees (about 7.7 km), for a 1228 by 528 px map zone.
- Query Overpass in two tiers, in this order, and save the raw JSON
  beside the output for audit. These are working files, not
  deliverables:
  - Major: `way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"](south,west,north,east); out geom;`
  - Minor: `way["highway"~"^(unclassified|residential|road|living_street)$"](south,west,north,east); out geom;`
- Overpass is flaky: a 502 or a timeout is not proof that the roads
  do not exist. Retry the same tiered query up to four times, with a
  few seconds between attempts, before concluding anything.
- If real road data cannot be fetched after those retries, say so
  plainly. Do not fall back to random contours and call the result a
  map. Offer a schematic version only if the user explicitly accepts
  it, labelled schematic and not to scale.
- Draw minor roads first (thin, faint), then major roads on top.
  In the working Bijie version: minor width 1, alpha about 110;
  motorway, trunk and primary width 2, alpha 205 to 225; secondary
  width 2, alpha about 185; tertiary width 1 to 2, alpha about 165.
  All in low-saturation off-white (238, 238, 232). No other road
  colours, no invented roads.
- Project each way's geometry with a linear lon/lat projection into
  the map rectangle. A nearby place label must be placed at its own
  projected coordinates, never hand-placed in a convenient direction.
- A sparse road network in a suburban or mountain-edge photo is a
  real result, not a drawing failure. Do not densify it by hand.
  Say so when you deliver, as was done for Bijie versus Xi'an's
  inner-city grid.

## Layout (Xi'an reference layout, the default)

- Map zone: sky, sea or other negative space, roughly the top third
  of the frame (Bijie: left 0.04, right 0.97, top 0.03, bottom 0.33
  as fractions of width and height). No square map card, no bounding
  box.
- Edge fade: fade the road layer out over about 70 px inside the map
  rectangle, with a smoothstep, so the map dissolves into the photo.
  Labels, title, compass and scale bar are drawn after the fade, so
  they stay readable.
- Title: serif capitals, letter-spaced, top left of the map zone
  (DejaVuSerif-Bold). Bijie: "B I J I E".
- Coordinates below the title, to two decimal places, in the
  reference format, for example "27.28° N    105.30° E". A smaller
  second line carries altitude and direction only when EXIF verified
  them, for example "1766 m  ·  62° NE".
- Compass rose on the left, over the map: a thin circle, a four-point
  star, and N, E, S, W in serif. Not a small north arrow alone.
- Scale bar below the compass: ticks at 0, 1, 2 and the full scale
  (default 4 km). Compute pixels per kilometre from the map width:
  `px_per_km = map_width_px / map_width_km`, where
  `map_width_km = lon_span * 111.32 * cos(mean_latitude)`.
  Do not copy another photo's pixel length.
- Shooting point: one red dot (193, 39, 45) with a white ring, at the
  projected EXIF point, with its verified place label next to it
  (Bijie: "Biyang"). A verified nearby place gets a small white dot
  at its projected coordinates and a short label (Bijie: "Caodi",
  about 1.5 km south-east, calculated from coordinates).
- Keep the number of labels small: city, shooting-point place, and
  at most one or two verified nearby places. Every label gets a
  thin dark stroke where a road line could cross it.
- Add only a very light paper grain, about 3 percent, so the print
  texture does not change the original colour or light.
- Keep the original width, height and aspect ratio unchanged, and
  keep the map off the main subject, the foreground and the horizon
  light that makes the photo work.

## Build with the helper

- Call the helper at
  `~/workspace/custom-skills/editorial_geo_overlay/scripts/make_editorial_geo.py`
  with a config file that lists only verified values: geo bbox,
  map rectangle, title, coordinates, subline, viewpoint lon/lat/label,
  nearby places with lon/lat/label, and scale kilometres.
  See `references/example-config.json` for the current format.
- Do not hardcode one photo location into the helper. The helper
  takes the bbox, the two Overpass JSON files and the config as
  arguments, and it writes only the finished picture.
- The old contour helper is retired. Do not call it, do not copy its
  random-ring code, and do not present its output as a geographic map.

## Inspect the result and deliver

- Open the finished picture with `muse.read` and look at it before
  you send it.
- Check, in this order: is this a real road map or a pattern? Is the
  title, compass and scale bar readable? Is any label crossed by a
  road line in a way that breaks reading? Does any map line cover
  the main subject? Do the roads fade at the edges with no box?
- Move a label into the dark part of the sky, thin a road class, or
  shrink the map zone when a check fails, then rebuild and look again.
  Do not deliver a version you have not looked at.
- Check that the mountains, buildings, sky and foreground are still
  the original photo, apart from the overlay area and the light grain.

## Deliver only the main image

- Deliver the finished picture as an attachment in the same message
  that announces it, and deliver nothing else as a picture.
- Do NOT attach, link or offer as a deliverable: the transparent
  map layer, a dark-background preview of the layer, the Overpass
  JSON files, or the build script. Those are working files. Keep
  them beside the output for later adjustment, but do not output them.
- If the user explicitly asks for the layer later, provide it then,
  with a note that white lines on transparency look blank on a light
  background. Until then, silence about the layer is correct.
- Tell the user in plain words what came from EXIF, what came from
  the map lookup, what came from the real road data, what is
  schematic (if anything), and what you did not verify. If the road
  network is sparse for a real reason, say so in one sentence.

## Available connectors

- [Places](/opt/hatch/connectors/places/CONNECTOR.md) for place details
  that can help identify a venue in a photo.

- Use `muse.connector_search` to find other connectors and
  `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP
  server and set it up with
  [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md),
  or build a custom connector.

## Websites

- OpenStreetMap is good for reverse geocoding a GPS point and for
  checking the nearest peak, scenic area and road.
- OpenStreetMap Overpass API is the source for the real road network
  in Step 3. Carry the exact latitude and longitude into the query,
  ask for geometry, and retry on 502 or timeout before giving up.
- Carry the exact latitude and longitude into the `browser.browse`
  task for Nominatim, ask for the full hierarchy and the nearest
  named features, and ask the browser to report what it did not find
  as well as what it found.
