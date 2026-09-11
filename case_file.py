"""
CASE: The Missing Midnight Muse
Original case, built for the AI Mystery Detective Team workshop.
Not the Aurora Diamond case — different setting, object, suspects and evidence.

Satisfies workshop deck (slide 7) case-design rules:
- Clear incident + time window
- 3-4 suspects
- Plausible motive per suspect
- Access, opportunity, alibi details per suspect
- Evidence with timestamps
- At least one misleading clue (H)
- One unresolved question (stated explicitly at the end)
- Rule against invented evidence (stated explicitly at the end)
"""

CASE_FILE = '''
CASE: The Missing Midnight Muse

At 7:00 PM, Ashford Gallery unveiled the painting "Midnight Muse" in the East
Wing for a private pre-auction preview. At 7:45 PM, a scheduled fire alarm
test triggered a gallery-wide evacuation lasting six minutes, ending at 7:51
PM. At 8:00 PM, staff returning to the East Wing found the frame on the wall
empty — the canvas had been cut out. No glass was broken and the frame itself
was undamaged.

SUSPECTS
1. Priya Desai, gallery director. Motive: the gallery faces bankruptcy; an
   insurance payout on the painting would keep it open. Says she was in her
   office finalizing auction paperwork. Her office keycard logged entry at
   7:40 PM, with no logged exit until 8:05 PM.
2. Marcus Webb, head security guard. Motive: recently passed over for
   promotion. Says he was monitoring lobby cameras during the alarm. Lobby
   footage shows him at the console continuously from 7:40-7:55 PM, but the
   East Wing camera feed was offline for scheduled maintenance during that
   window.
3. Elena Cruz, art restorer. Motive: significant personal debt from an
   ongoing legal case. Says she was in the restoration workshop the entire
   time. Her badge unlocked the workshop at 7:15 PM and the East Wing
   service door at 7:47 PM.
4. Julian Roth, collector bidding on the piece. Motive: wanted the painting
   without paying the auction price; a pre-auction offer he made was
   rejected by the gallery the week before. Says he was in the courtyard
   smoking with two other guests from 7:42-7:53 PM. Two guests confirm this.

EVIDENCE
A. Fire alarm system log — confirms the 7:45-7:51 PM test was scheduled and
   gallery-wide, triggered automatically, not manually.
B. East Wing service door access log — Elena's badge opened this door at
   7:47 PM.
C. Elena's statement — she says her badge remained clipped to her lab coat
   in the workshop the entire time and was never in her hand near the East
   Wing.
D. Frame examination — the canvas was cut from the stretcher bars with a
   sharp blade; no glass broken, frame undamaged.
E. Trace evidence — a small smear of white restoration-grade gesso, a
   material used only in the restoration workshop, was found on the East
   Wing doorframe.
F. Julian's rejected pre-auction offer — documented in gallery records,
   dated one week before the incident, roughly 20% below the painting's
   estimated value.
G. Insurance policy — payout on the painting goes to the gallery's parent
   trust, not to any individual named suspect.
H. Loading dock camera — an unidentified delivery driver dropped off crates
   at 7:50 PM. Gallery delivery records confirm this matches a routine
   weekly delivery, unconnected to gallery staff or the East Wing.

UNRESOLVED QUESTION
No camera captured the painting leaving the building, and it is unconfirmed
whether Elena's badge was used by her personally or by someone else who had
access to it during the evacuation.

RULES
Use only this case file. Separate facts from inferences. Mention
uncertainty. Do not invent evidence, witnesses or events not stated here.
This is a fictional educational exercise.
'''

# Variant for the workshop's "change one clue, compare results" exercise.
# Removes Evidence E (the gesso trace), the clue most directly tying Elena
# to the East Wing beyond the badge log alone.
CASE_FILE_VARIANT = CASE_FILE.replace(
    '''E. Trace evidence — a small smear of white restoration-grade gesso, a
   material used only in the restoration workshop, was found on the East
   Wing doorframe.
''',
    ''
)
