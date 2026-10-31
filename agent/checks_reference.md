# Check language

A check is a JSON object `{"id": "<snake_case>", "description": "<the design rule>",
"violation": <expr>}`. The `violation` expression is evaluated by a deterministic interpreter
(no LLM, no code execution) over the **trace** of one attempt: the state right after a level
load, then the state after every action. It is true when the attempt shows the rule broken.

Each state looks like `GetState`: `PawnAlive` (bool), `PlayerLocation` {X,Y,Z}, `LastZ`,
`KillZ`, `InventoryCount` (int), `ActorStates` {name: "open" | "closed" | "present"} (a
collected or destroyed object is absent, so its value is `null`), `ActorLocations`
{name: {X,Y,Z}}. Coordinates are in cm.

## Values

- Literals: numbers, strings, `true`, `false`, `null`.
- `{"var": "ActorStates.IronGate"}`: a dotted path into the current state. A missing key
  gives `null`.
- `{"prev": "<path>"}`: the same path in the previous state (`null` at the first state).
- `{"first": "<path>"}`: the path in the first state (right after the level load).
- `{"did": "interact"}`: true if the action that produced the current state is of that type
  (`move_to`, `look_at`, `jump`, `interact`, `step`). Actions take effect during the next
  `step`, so to test what an action caused, look at a later state.
- `{"dist": ["PlayerLocation", "ActorLocations.IronGate"]}`: 3D distance in cm between two
  location paths of the current state (`null` if either is missing).

## Operators

- Comparison: `{"==": [a, b]}`, `{"!=": [a, b]}`, `{"<": [a, b]}`, `{"<=": [a, b]}`,
  `{">": [a, b]}`, `{">=": [a, b]}`. Ordering comparisons with a non-number are false.
- Arithmetic: `{"+": [a, b]}`, `{"-": [a, b]}` (`null` if either side is not a number).
- Logic: `{"and": [...]}`, `{"or": [...]}`, `{"not": e}`.

## Time

The top-level expression is evaluated at the **last** state. These change which state is
"current" for the expression inside them:

- `{"ever": e}`: `e` holds at some state of the trace.
- `{"always": e}`: `e` holds at every state.
- `{"final": e}`: `e` holds at the last state.
- `{"after": [a, b]}`: `a` holds at some state *i* and `b` holds at the last state, with the
  last state later than *i*. Use it for "after doing X, Y must eventually be true".

## Examples

A locked door must not open while its key is still in the world:

```json
{"id": "gate_needs_key", "description": "The iron gate stays locked until the iron key is picked up.",
 "violation": {"ever": {"and": [{"==": [{"var": "ActorStates.IronGate"}, "open"]},
                                {"==": [{"var": "ActorStates.IronKey"}, "present"]}]}}}
```

The other side of the same rule: interacting with the gate from up close while carrying the
key must open it:

```json
{"id": "gate_opens_with_key", "description": "With the iron key, interacting with the iron gate opens it.",
 "violation": {"after": [{"and": [{"did": "interact"}, {"==": [{"var": "ActorStates.IronKey"}, null]},
                                  {"<": [{"dist": ["PlayerLocation", "ActorLocations.IronGate"]}, 150]}]},
                         {"==": [{"var": "ActorStates.IronGate"}, "closed"]}]}}
```

Collecting an apple must add exactly 1 to the inventory:

```json
{"id": "apple_worth_one", "description": "An apple adds 1 to the inventory.",
 "violation": {"ever": {"and": [{"==": [{"prev": "ActorStates.Apple"}, "present"]},
                                {"==": [{"var": "ActorStates.Apple"}, null]},
                                {"!=": [{"-": [{"var": "InventoryCount"}, {"prev": "InventoryCount"}]}, 1]}]}}}
```
