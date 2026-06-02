# Site viewer hotfix

This hotfix stabilizes the static GitHub Pages viewer after the introduction of meeting relation exports.

## Problem

The relation-aware viewer could load `latest.json`, but the document table and pagination were fragile after the relation context changes. The site also did not clearly show whether the current document set actually matched the relation export window.

## Changes

- Replaced fragile table `innerHTML` rendering with DOM-based table row and cell creation.
- Added a robust JSONL parser that supports normal JSONL, JSON arrays, and concatenated JSON objects as a fallback.
- Kept relation files optional, so the viewer keeps working if relation exports are missing.
- Added support for both `latest.outputs` and the older `latest.exports` manifest shape.
- Added a status summary showing how many displayed documents have relation matches.
- Added lightweight static tests for the viewer script.

## Notes

The current public data may contain a small latest document window and a separate relation scan window. It is therefore possible to have relation exports available while only a subset, or none, of the currently displayed documents has a relation match.
