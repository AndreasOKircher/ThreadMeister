# Triage labels

The Matt Pocock skills speak in terms of canonical triage roles. This repo uses the same
strings.

| Label in mattpocock/skills | Label here        | Meaning                                  |
| -------------------------- | ----------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`    | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`      | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent` | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human` | Needs a human (e.g. a Fusion smoke test) |
| `wontfix`                  | `wontfix`         | Will not be actioned                     |

## Additional labels

| Label         | Terminal? | Meaning |
| ------------- | --------- | ------- |
| `proposed`    | no        | Sketched idea, not yet triaged — weaker than `needs-triage`. |
| `needs-grill` | no        | The goal is clear; the design needs a `/grill-me` session first. |
| `on-branch`   | no        | Claimed; in flight on a feature branch. |
| `deferred`    | no        | Real, deliberately parked. Must say what would un-park it. |
| `completed`   | yes       | Implemented, committed, tests pass. |
| `superseded`  | yes       | A later decision removed the subject. Name what superseded it. |
| `closed`      | yes       | Folded into another issue, or answered without work. Name where. |

Terminal means terminal: never reopen — file a new issue.

## `Status:` line format

Keep the label alone on the line. Put reasoning in a note below:

```markdown
Status: deferred

> **Status note.** Waiting for the Fusion API to expose X; un-park when it ships.
```
