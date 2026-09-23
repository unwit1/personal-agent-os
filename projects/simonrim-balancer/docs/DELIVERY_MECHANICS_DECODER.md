# Projectile / Explosion / Hazard Delivery Decoder — 2026-09-23

This checkpoint decodes gameplay delivery objects from the supplied Simonrim snapshot using current xEdit TES5 definitions.

## Coverage

- PROJ: 76 / 76 decoded (92-byte full layout), 0 failures.
- EXPL: 76 / 76 decoded (52-byte full layout), 0 failures.
- HAZD: 47 / 47 decoded (40-byte full layout), 0 failures.
- Repeated typed profiles with sample size >= 3: 22.
- Approved rules: 0.

Projectile types in the supplied corpus:
- Lobber: 39
- Missile: 22
- Flame: 8
- Beam: 5
- Cone: 2

The decoder preserves projectile flags/type, gravity, speed, range, explosion links, force/collision/lifetime parameters, explosion damage/radius/flags, and hazard radius/lifetime/interval/inheritance behavior plus canonical Form relationships.

## Exact imported-baseline deltas

Five delivery records have an exact prior imported Simonrim baseline, and all five are materially changed:

1. Adamant `MAG_ProjectileRunePoison01`
   - redirects its explosion from the Mysticism poison-rune explosion to an Adamant-owned explosion.

2. Adamant `MAG_ExplosionRuneShock02`
3. Adamant `MAG_ExplosionRuneFlame02Dualcast`
4. Adamant `MAG_ExplosionRuneShock02DualCast`
   - each adds the Explosion flag `Ignore LOS Check` relative to the imported Mysticism baseline.

5. Adamant `MAG_CircleOfProtectionHazardDualCast`
   - lifetime changes from 60 to 75 seconds.
   - spawned spell reference changes from a Mysticism-owned spell to Skyrim.esm:04E80D.

These are exact implementation deltas. They are not automatically generalized into suite-wide rules.

## Guardrails

- Visual/audio references remain linked as provenance but are not treated as balance values.
- Repeated projectile/explosion/hazard profiles are observations only.
- External Skyrim/DLC baselines remain unknown where their record bodies are not in the supplied snapshot.
- No delivery observation is an approved rule.
