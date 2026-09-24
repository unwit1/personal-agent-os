# powerofthree's Papyrus Extender v6.5.2 — Event Surface Index

Imported: 2026-09-24
Release: `v6.5.2`
Status: version index; exact event tables live in the canonical provider event file

## Canonical detail

Use:
`po3-papyrus-extender-event-catalog.md`

It contains the exact registration and callback declarations for:
- Form receivers;
- Alias / ReferenceAlias receivers;
- ActiveMagicEffect receivers.

## v6.5.2 facts

Each provider script declares **37 events** and **69 registration/helper declarations**.

The same logical event can be registered to different receiver lifetimes, which matters for:
- save persistence;
- alias fill/clear;
- ActiveMagicEffect teardown;
- stale event registrations after updates.

## Source-name caveat

v6.5.2 preserves a real source difference:

- Alias callback: `OnShoutAttack(Shout akShout)`
- Form callback: `OnPlayerShoutAttack(Shout akShout)`
- ActiveMagicEffect callback: `OnPlayerShoutAttack(Shout akShout)`

Do not normalize those names in generated code.

## Related

- `../sources/papyrus-extender-v6.5.2-manifest.md`
- `po3-papyrus-extender-api-signatures.md`
- `papyrus-event-registration-messaging.md`
