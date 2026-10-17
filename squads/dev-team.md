Test-first delivery. Your own instructions are authoritative; this is the shape they sit in.

- Three issue levels: **spec** (yours) → **ticket** (`sq-verifier`) → **handoff** (its assignee).
- Every ticket has the same two stages: **test** (`sq-test-writer`) then **implement** (`sq-implementer`). Nothing else.
- The independent check is structural, not an extra pass: the tests are written before the code, by an agent that never sees it, and the implementer may never weaken one.
- `done` is the only verb a member has. No `@mention`, no `blocked`, no comment on an issue it does not own.
- Every start and restart is two writes: `backlog`, then `todo`.
- One spec at a time, one ticket at a time.
