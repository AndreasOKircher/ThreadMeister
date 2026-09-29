# duplicate-install

Found while testing the 1.2.3 fix (2026-09-28) and hit again by the GitHub #1 reporter
(2026-09-29): with two ThreadMeister copies installed (App Store bundle + manual install),
both register the command ID `ThreadMeisterCmd`. The copy that loads first owns the toolbar
button; the other one fails with "a command definition with that id already exists". Users
keep running the old code and still see the bug the new version fixes.

Fusion's Add-Ins list shows both copies (e.g. 1.2.0 and 1.2.3); only disabling the old one
at startup and restarting Fusion helped.
