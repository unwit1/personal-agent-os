# Minifigure Decoration Grammar

## Purpose
Teach an AI the visual language of minifigure-scale decoration without treating copyrighted character artwork as reusable production art.

## Learnable feature classes
### Head
eye landmarks
pupil/highlight conventions
eyebrow placement
mouth/nose simplification
facial-hair zones
wrinkle/scar/freckle primitives
eyewear landmarks
front/back secondary expressions
wrap seam behavior

### Torso
neck opening relationship
collar/lapel/hood/scarf grammar
shirt/jacket/armor layering
belt and waist transitions
pockets/fasteners
fabric folds
emblems/badges
printed-vs-sculpted boundary
front/back continuation
side print continuation

### Arms
sleeve boundaries
gauntlets/gloves
tattoos/markings
shoulder insignia
curvature compensation

### Hips/legs
belt continuation
coat tails
pockets
knee details
boots/shoes
left/right continuity
side-leg continuation

## Dataset representation
Do not store only finished raster examples. Extract measurable primitives:
- normalized landmark coordinates
- line-width classes
- fill regions
- symmetry relationships
- semantic labels
- color-role labels
- overlap/layer ordering
- edge-distance/safe-zone statistics
- wrap relationships.

## Style profiles
Allow multiple profiles rather than one “LEGO style”:
classic-simple
modern-detailed
licensed-character-like abstraction
military/fantasy/sci-fi custom
high-detail collector custom
user-house-style

Profiles should be descriptive and learned from permitted observations; they should not copy a particular protected character design.

## Accuracy tests
A generated decoration should be scored for:
- landmark placement
- line-width consistency
- readability at physical size
- symmetry
- continuity across part boundaries
- safe-zone compliance
- UV-printability
- color count/opacity requirements.

## Production handoff
Generated art remains a candidate until converted to clean vector paths, checked at actual scale and assigned explicit CMYK/white/varnish behavior.
