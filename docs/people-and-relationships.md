# People and relationship intelligence

Status: initial implementation 2026-09-25

## Purpose

Agent OS needs to remember people without turning every name, mailbox, photo,
or account observation into a confident relationship claim. The canonical
boundary is therefore split:

- sanitized durable relationship summaries may live in Git;
- aliases, contact identifiers, raw evidence, private third-party details, and
  high-volume observations live in `.agent-local/people/people.sqlite3`;
- uncertain identity matches remain candidates.

## Identity is not relationship

Two independent confidence values are retained:

1. **identity confidence** — how sure are we that this observation belongs to
   this person?
2. **relationship confidence** — how sure are we that the claimed relationship
   type/state is correct?

A known identity can still have an uncertain relationship. Interaction
frequency does not by itself mean friendship, closeness, or importance.

## No same-name merging

A first name or even a full-name match is insufficient for destructive merge.
The local store returns every matching alias candidate. Stable identifiers,
organization/time context, multiple independent observations, or user
confirmation are needed to link profiles.

This protects cases such as a personal Olivia versus an Olivia in a work
archive, and current coworkers whose names also occur in older organizational
mail.

## Source actors

Evidence records use one of:

- `user`
- `user_confirmed`
- `other_account_user`
- `third_party`
- `organization_archive`
- `automated`
- `unknown`

Owning an account is not proof of authorship. Shared ChatGPT accounts, shared
mailboxes, imported PSTs, applicant records, forwarded mail, and inherited
organizational archives must resolve actor/subject before they can change the
personal profile.

Only direct user/user-confirmed actor evidence is eligible for direct personal
profile promotion. Other actor classes remain review/reconciliation evidence.

## Local schema

`src/agent_os/people.py` provides local tables for:

- people;
- aliases;
- relationships with temporal bounds;
- provenance evidence;
- unresolved identity candidates.

Raw contact details should be attached only in local extensions/evidence stores,
not copied into Git-backed relationship summaries.

## Current sanitized reconciliation

`profile/relationship-context.json` contains the current low-risk summary:
Olivia's dated/current relationship context, broad sibling structure, source
attribution policy, quarantined biography claims, and unresolved identity
candidates. Quarantined and unresolved sections are excluded from selective
profile retrieval.
