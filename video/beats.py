"""The demo's storyboard: one narration line per beat and what is on screen meanwhile.

kind "card": slide <slide> of video/deck.html at <step>.
kind "clip": a replay video; "tiles": the same replay three times; "turns": the session's
screenshots with the model's plan; "shot": one screenshot under a deck overlay.
"""

BEATS = [
    # 1. The problem
    ("Games ship with bugs because testing is slow and manual.",
     {"kind": "clip", "video": "bug3", "overlay": ("hook", 1)}),
    ("A human reads the design document, plays the level, and checks every rule by hand.",
     {"kind": "card", "slide": "manual", "steps": [1, 2, 3]}),
    ("Small studios often have no QA team at all.",
     {"kind": "card", "slide": "manual", "steps": [4]}),
    ("I built an agent that does that job in Unreal Engine 5, with Meta's Muse Spark.",
     {"kind": "card", "slide": "title", "steps": [1]}),
    # 2. From a design document to checks
    ("The input is the level's design document, in plain English.",
     {"kind": "card", "slide": "doc", "steps": [1]}),
    ('For example: "A door opens only with the key of the same color."',
     {"kind": "card", "slide": "doc", "steps": [2]}),
    ("Muse Spark reads the document and writes its own checks, in a small JSON language.",
     {"kind": "card", "slide": "doc", "steps": [3, 4]}),
    ("The model never runs code. A simple interpreter evaluates these checks on the game state.",
     {"kind": "card", "slide": "eval", "steps": [1, 2, 3]}),
    # 3. The agent plays
    ("Then the agent plays the level.",
     {"kind": "card", "slide": "pipeline", "steps": [3]}),
    ("Every turn, Muse Spark sees a screenshot and the game state.",
     {"kind": "shot", "turn": 22, "overlay": ("sees", 1)}),
    ("It decides what to do: walk to a key, pick it up, try a door.",
     {"kind": "turns", "turns": [22, 23, 24, 25]}),
    ("It always says which rule it is testing.",
     {"kind": "turns", "turns": [26], "rule": "door_needs_own_key"}),
    ("When a rule breaks, it files a bug.",
     {"kind": "turns", "turns": [27]}),
    ("Here it found that the red door ignores the red key, but opens with the green one.",
     {"kind": "clip", "video": "bug3", "overlay": ("found", 1)}),
    ("A simple bot can't find that bug. It needs a plan: pick up the right key, then try the "
     "door.",
     {"kind": "card", "slide": "plan", "steps": [1, 2, 3]}),
    # 4. The verifier
    ("But models make mistakes, so the agent's word is not enough.",
     {"kind": "card", "slide": "pipeline", "steps": [4]}),
    ("A verifier with no AI reloads the level and replays the exact actions three times.",
     {"kind": "tiles", "video": "bug3", "overlay": ("tiles", 1)}),
    ("A bug is confirmed only if it fails all three times.",
     {"kind": "tiles", "video": "bug3", "overlay": ("tiles", 2), "freeze": True}),
    ("In one session, Muse Spark reported a door that wouldn't open.",
     {"kind": "card", "slide": "reach", "steps": [1]}),
    ("It was standing too far away. The replay rejected it.",
     {"kind": "card", "slide": "reach", "steps": [2, 3]}),
    # 5. Results
    ("To measure what the AI adds, I compared it against a scripted bot.",
     {"kind": "card", "slide": "versus", "steps": [1]}),
    ("The bot gets the same checks the AI wrote, and the same map sweep.",
     {"kind": "card", "slide": "versus", "steps": [2]}),
    ("On the Vault, Muse Spark found the red door bug six times out of six.",
     {"kind": "card", "slide": "versus", "steps": [3]}),
    ("The scripted bot: zero out of six.",
     {"kind": "card", "slide": "versus", "steps": [4]}),
    ("Then I froze the agent and tested it on a new level, the Armory, that it had never seen.",
     {"kind": "card", "slide": "armory", "steps": [1]}),
    ("Muse Spark Open, Meta's open-weights model on Baseten, found all three bugs in every "
     "session.",
     {"kind": "card", "slide": "armory", "steps": [2]}),
    ("Each session costs less than forty cents.",
     {"kind": "card", "slide": "armory", "steps": [3]}),
    # 6. Limits and close
    ("It's not perfect. Results vary between sessions, and two wrong checks were confirmed in "
     "thirty-four runs.",
     {"kind": "card", "slide": "limits", "steps": [1, 2]}),
    ("Every run is in the repository, so you can check the numbers yourself.",
     {"kind": "card", "slide": "limits", "steps": [3]}),
    ("Everything here was built during the hackathon: the levels, the agent and the verifier.",
     {"kind": "card", "slide": "built", "steps": [1]}),
    ("Parts of the code were written by Muse Code.",
     {"kind": "card", "slide": "built", "steps": [2]}),
    ("A designer writes the rules. The AI tests them.",
     {"kind": "card", "slide": "end", "steps": [1, 2], "hold": 3.5}),
]
