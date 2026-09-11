"""
CASE: The Vanishing Aurora Diamond
Verbatim case file from AI_Mystery_Detective_Team.ipynb for the AI Mystery Detective Team workshop.

Satisfies workshop deck case-design rules:
- Clear incident + time window
- 3-4 suspects
- Plausible motive per suspect
- Access, opportunity, alibi details per suspect
- Evidence with timestamps
- Misleading clue
- Unresolved question / rules stated explicitly at the end
- Rule against invented evidence
"""

CASE_FILE = '''
CASE: The Vanishing Aurora Diamond
At 8:00 PM, curator Dr. Mira Sen displayed the Aurora Diamond inside a locked glass case at Northbridge Museum. At 8:20 PM, a power failure darkened the gallery for four minutes. At 8:30 PM, the diamond was gone. No glass was broken.

SUSPECTS
1. Lena Ortiz, security chief. Motive: recently denied a promotion. Says she was restarting the basement generator from 8:19–8:26. Her access card opened the basement at 8:20.
2. Theo Park, visiting magician. Motive: publicity. Says he remained on stage rehearsing. A stage camera shows him continuously from 8:15–8:29.
3. Arjun Vale, assistant curator. Motive: large private debt. Says he was cataloguing artifacts in the archive. His access card opened the archive at 8:12 and the gallery display case at 8:23.
4. Sofia Reed, journalist. Motive: wanted an exclusive story. Says she was interviewing guests in the lobby. Three guests remember speaking with her during the blackout.

EVIDENCE
A. The display case uses an electronic lock and records every valid access card, even during a power failure because it has a battery.
B. The log records Arjun's card opening the case at 8:23 PM.
C. Arjun says his access card was in his jacket inside the archive.
D. A hallway camera resumes at 8:25 and shows Arjun leaving the archive carrying a flat catalog folder.
E. Blue velvet fibers were found inside that folder. The diamond's display cushion is blue velvet.
F. A muddy shoeprint near the case matches Lena's boot size, but maintenance records show Lena inspected the same case after walking through a wet courtyard that afternoon.
G. The diamond was insured, but the policy pays the museum—not any suspect.

RULES
Use only this case file. Separate facts from inferences. Mention uncertainty. Do not invent evidence. This is a fictional educational exercise.
'''

# Variant for the workshop's "change one clue, compare results" exercise.
# Removes Evidence E (blue velvet fibers).
CASE_FILE_VARIANT = CASE_FILE.replace(
    "E. Blue velvet fibers were found inside that folder. The diamond's display cushion is blue velvet.\n",
    ""
)
