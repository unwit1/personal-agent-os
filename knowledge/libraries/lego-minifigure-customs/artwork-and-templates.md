# Artwork and Templates

## Master-file rule
Use vector masters where practical (SVG/AI/Affinity/Inkscape). Keep layers for boundaries, safe area, bleed, base color, white underbase, keyline, spot colors, highlights/shadows, registration and notes. Export process-specific PNG/PDF from the master.

BrickLink Studio's decorated-minifig guide specifies PNG input and gives a head canvas reference of 416 × 320 px with face features around 193 × 142 px, while explicitly describing the guide as reference rather than a definitive production standard. Use it for visualization, not as a physical manufacturing specification.

## Physical templates
Build templates in millimeters and derive pixels from DPI. Lock printer scaling to 100% / Actual Size; never Fit to Page. Maintain templates for torso front/back, head front/back/wrap, arms, hip, leg fronts/sides, shields/tiles/accessories and cape/cloth cuts.

Each template needs centerline, physical dimensions, safe area, bleed, seam/wrap overlap, registration marks, calibration ruler and version. Community customizers commonly use 600 dpi as a useful raster starting point; vector masters remain preferable.

## White underbase and registration
For transparent media/direct printing, create a white-underbase layer beneath colors needing opacity. Slightly choke underbase to prevent white halos if registration shifts. Exact choke is process-specific and must be calibrated. Save jig coordinate system, origin, printer profile and jig version.

## Validation
Print a known ruler/grid at 100%, measure with calipers, correct the workflow scale, then test the outline on a sacrificial part. Photograph and record every template revision.

Naming: project_character_part_surface_art-v###_process_profile.ext

Sources:
https://studiohelp.bricklink.com/hc/en-us/articles/5877834417303-Creating-a-decorated-minifig
https://www.eurobricks.com/forum/forums/topic/156058-where-to-start-with-custom-minifigure-printing/
