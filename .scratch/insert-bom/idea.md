# insert-bom

Scan the timeline for ThreadMeister Timeline Groups — named `(<count>x <insert name>)`
(`core/tm_execute.py:150`) — and report a count per insert size: "you need 12× M3 standard,
4× M5 short". Useful before ordering or printing.

## Open questions

- Groups can be renamed or deleted by the user — rely on names, or tag features with attributes (`attributes.add`)?
- Suppressed features: count or skip?
- Output: message box, copyable text, CSV?

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
