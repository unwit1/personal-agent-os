# Minifigure Customs Knowledge Ontology

The Knowledge Engine should normalize incoming information into these linked entities.

## Core entities
- PartDesign
- Element
- MoldVariant
- DecoratedPart
- MinifigureAssembly
- Color
- Material
- Finish
- Artwork
- PrintSurface
- Template
- CharacterDesign
- Pose
- CameraPreset
- RenderAsset
- UVPrintProfile
- Jig
- JigCavity
- Printer
- InkSet
- RIPProfile
- Primer
- Varnish
- Resin
- ResinPrintProfile
- Connector
- FitCoupon
- Supplier
- Batch
- Experiment
- Defect
- QCResult
- Product
- Source
- RightsRecord

## Important relationships
PartDesign HAS_VARIANT MoldVariant
Element REALIZES PartDesign
DecoratedPart DECORATES PartDesign
PartDesign MADE_OF Material
PartDesign AVAILABLE_IN Color
MinifigureAssembly CONTAINS PartDesign
Artwork TARGETS PrintSurface
Template MAPS PrintSurface
Jig HOLDS PartDesign
UVPrintProfile USES Jig
UVPrintProfile USES InkSet
UVPrintProfile TARGETS Material
Connector MATES_WITH PartDesign
ResinPrintProfile VALIDATES Connector
Batch USES Artwork
Batch USES UVPrintProfile
QCResult EVALUATES Batch
RenderAsset DERIVED_FROM PartDesign
RenderAsset CONDITIONS GenerationRequest
Source SUPPORTS every factual assertion.

## Confidence
authoritative
manufacturer
catalog-high
community-corroborated
empirical-user-validated
inferred
unverified

## Version applicability
Every technical fact that can change must support valid_from, valid_to, source_date and last_verified.

## AI retrieval policy
A generation model should receive only the relevant slice:
1. target part geometry,
2. target colors/materials,
3. style grammar,
4. target manufacturing profile,
5. applicable constraints,
6. character references,
7. prior validated experiments.

Do not dump the entire library into the prompt.
