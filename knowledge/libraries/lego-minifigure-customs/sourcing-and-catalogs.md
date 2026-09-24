# Sourcing and Catalogs

## Core sources
LEGO Pick a Brick: current genuine elements; filter by category/color, search by piece/set, bulk list upload. https://www.lego.com/en-us/pick-and-build/pick-a-brick

BrickLink: collector marketplace/catalog for parts, minifigures, inventories, colors and historical availability. https://www.bricklink.com/ and https://v2.bricklink.com/en-us/catalog/color-guide

Rebrickable: structured catalog/API for official sets, parts, minifigs and colors; supports external IDs. For bulk ingestion use downloadable datasets rather than repeated API calls. https://rebrickable.com/api/v3/docs/ and https://rebrickable.com/downloads/

Brickognize: photo candidate identification for parts/minifigs/sets/sticker sheets. Confirm before canonicalizing. https://brickognize.com/

LDraw: open geometry ecosystem useful for part references/rendering/color mapping. https://www.ldraw.org/

BrickLink Studio: digital assembly/decorated-minifigure preview. https://www.bricklink.com/v3/studio/download.page

## Supplier records
Record category, URL, region, genuine-vs-compatible policy, MOQ, unit cost, shipping, lead time, consistency, return policy and last verification.

## Cost model
donor parts + decoration + accessories + cloth + packaging + consumables + spoilage + labor + setup amortization + marketplace/payment fees + shipping materials.

## Provenance
Record genuine/compatible status per component. Never collapse them. Cache catalog IDs and acquisition date; price/availability are time-sensitive observations, not permanent facts.

Agent OS should normalize identifiers, preserve source/timestamp and keep historical observations so sourcing recommendations can explain changes.
