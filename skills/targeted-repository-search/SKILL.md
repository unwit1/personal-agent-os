---
name: targeted-repository-search
description: Search a repository narrowly by filenames, symbols, errors, references, and likely control points before opening broad file sets.
---

# Targeted Repository Search

Use before broad repository inspection.

Search in this order:

1. exact filenames, symbols, commands, error text, configuration keys, or known paths from the request;
2. references to the likely controlling function/class/module;
3. nearby tests and documentation;
4. only then broader architectural files if a concrete gap remains.

Rules:
- open the smallest number of files needed to establish control flow and constraints;
- prefer snippets/search matches before fetching full files;
- do not read the whole repository as a default discovery strategy;
- stop repository discovery once the implementation path and required validation are clear;
- use `change-scope-minimizer` before edits.

If broad inspection is genuinely required, state the reason.
