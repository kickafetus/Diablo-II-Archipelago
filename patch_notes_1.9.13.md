# Diablo II Archipelago — Beta 1.9.13

A bug-fix-focused release. Most of these came from Marco's own
hands-on testing plus a full line-by-line internal code review of
several core systems; the final three — including what's likely the
single most disruptive bug in the game today — surfaced from a fresh
pass through Discord bug reports (Congree, danRolleikon, JETgroovy,
Pulsar, and Tall Sam all helped pin these down). Ten bugs closed in
total, plus some packaging hygiene aimed at antivirus false positives.

---

## Bug fixes

### Launcher shows the wrong installed version after updating, then closing the game

**Symptom:** After updating to a new build (e.g. 1.9.12), launching
the game and then closing it would make the launcher revert to
showing an old version — "Beta 1.9.4" — as installed, and prompt to
update all over again, even though the correct build was already
installed and running fine.

**Root cause:** Two coupled issues in the launcher's incremental
"Update Game" path (a fresh install was never affected — that path
always recorded its version correctly):

1. The launcher only wrote the new version number to its local
   bookkeeping file (`version.dat`) if literally every one of the
   ~890 game files re-downloaded with zero failures in a single pass.
   A single flaky download — a network hiccup, a temporary GitHub
   rate-limit, antivirus software holding onto one file for a moment —
   silently skipped recording the new version. This happened even
   though every file that DID come through was already verified
   byte-for-byte against the official manifest, and the actual game
   (DLL, data files, etc.) was correctly updated and fully playable.
2. Right after an update finished, the launcher unconditionally
   displayed "Ready to play" no matter what — so the mismatch stayed
   completely invisible until the next time the launcher window
   opened, which naturally happens right after a play session ("launch
   the game, then close it" is just normal use).

**Fix:** The launcher now always records the version it just finished
syncing to — every downloaded file is already SHA-256-checked against
the manifest as it lands, and the existing pre-launch verifier
independently re-checks and heals anything that's still wrong before
every single "Play" click, so this is safe to do unconditionally. The
post-update screen now always re-derives its status from what's
actually recorded on disk instead of assuming success, so on the rare
chance something is still out of sync, you'll see "Update Game"
immediately — not a false "Ready to play" that only corrects itself
on the next restart.

### Depositing a stack of stackable items (Skeleton Keys, Scrolls, Tomes, …) into the Consumables/Runes/Gems stash destroyed most of the stack

**Symptom:** Putting a stack of stackable items — Skeleton Keys,
Scrolls of Town Portal/Identify, Tomes, throwing potions,
arrows/bolts, and similar — into its matching slot in the
Consumables/Runes/Gems stash only ever credited that slot with **1**
unit, no matter how large the stack actually was, while the *entire*
physical stack vanished from the backpack in the same motion. A stack
of 14 Skeleton Keys, for example, banked as "1" — the other 13 were
simply gone. Pulling items back out of the slot afterwards only ever
returned the 1 unit that had actually been recorded; the rest was
unrecoverable.

**Root cause:** There are two ways to get an item into one of these
slots — the documented shift+right-click "quick deposit", and simply
dragging the item onto its slot by hand — and both had the exact same
flaw. Each correctly checked that the item belonged in that slot, then
always removed the *whole* physical stack from the backpack (correct)
but always credited the slot with exactly **+1** regardless of the
stack's real size (wrong for anything bigger than a single unit).
Single, non-stacking items — runes, gems, jewels, unique items, and so
on — were never affected, since "1 physical item = 1 banked unit" was
already the correct behavior for those.

**Fix:** Both deposit methods now read the stack's true size — the
very same number the game already shows you on the item's own tooltip,
e.g. "x14" — *before* the item leaves your backpack, and credit the
slot with that full amount in a single step. As an extra safety net,
if banking the whole stack would push a slot past its 999-item cap,
the deposit is now refused outright and nothing happens to your
items — instead of silently banking part of the stack and destroying
the rest, which would just be a smaller-scale repeat of the same bug.

### Skill panel could render with stale state and refuse to close on some PCs

**Symptom:** On certain computers, the skill panel overlay could
appear with incorrect information, and its close button would do
nothing — leaving the panel stuck open until the character was
reloaded.

**Root cause:** The overlay checked whether the game's own skill panel
was open by reading a fixed, hardcoded memory address. That address is
only valid when a particular game component (`D2Client.dll`) loads at
its default location in memory — true for most systems, but not
guaranteed. Certain other software running alongside the game (overlay
tools such as Discord/NVIDIA/AMD/MSI Afterburner, RGB controllers,
antivirus hooks, screen recorders, and similar) can cause Windows to
load that component at a different address instead. When that
happened, the hardcoded address pointed at unrelated data, so the
overlay worked from garbage information about the panel's actual
state.

**Fix:** The overlay now looks up the component's real, current
location at runtime and reads the flag relative to that — the same
safe approach already used everywhere else in the mod for this kind
of check — so the result is correct no matter where the component
ends up loading.

### Rare crash during zone transitions, unrelated to Zone Locking

**Symptom:** An occasional crash could occur while moving between
zones — including in situations that had nothing to do with the Zone
Locking gate system.

**Root cause:** Two separate pieces of internal code were both able to
react to "move the player to a new zone" requests — the kind generated
by Zone Locking redirects, Entrance Shuffle warps, and other internal
teleports — and both were capable of calling the underlying
game-engine relocation function for the very same request. Normally
only one of the two ever actually does anything, but on some PC setups
the second could also activate. When both fired for the same request
in close succession, the game engine ended up relocating the player
twice during a single transition, which corrupted its own internal
bookkeeping and crashed the game.

**Fix:** Removed the redundant listener so that exactly one piece of
code — the one verified to run consistently on every setup — now
owns zone-change requests from start to finish.

### Triggering a trap could occasionally summon an unexpectedly tough monster — including, rarely, right in the middle of town

**Symptom:** On certain computers, setting off one of the mod's "trap"
location checks could occasionally summon a single, much stronger
named monster in addition to the normal wave of enemies — and in rare
cases, drop that monster directly in town while you were shopping,
managing your stash, or talking to an NPC.

**Root cause:** Two completely separate pieces of internal code were
each able to react to the same triggered trap. The correct one — live
since version 1.8.5 — spawns a manageable pack of ordinary monsters
and properly waits until you've actually left town before doing so,
specifically so a trap can never be sprung on you mid-errand. A
second, leftover piece of code could *also* react to the very same
trigger, summoning a single far stronger named monster with none of
those safeguards — no town check, no waiting. Normally only the
correct path runs, but on some PC setups the leftover one could
activate as well, on the same trap.

**Fix:** Removed the leftover path entirely, so every triggered trap
now goes through the one piece of code verified to behave correctly
and consistently on every setup — the same kind of redundant-listener
problem, and the same fix, as the rare zone-transition crash above.

### Gold, stat points, and skill points from certain standalone-mode rewards could be queued up and then silently lost

**Symptom:** In standalone mode (playing without an active Archipelago
connection), gold/stat-point/skill-point rewards from certain
sources — Collection page bonuses, and the small "consolation"
rewards from Bonus and Extra Checks — could be queued up and visibly
counted in the on-screen display, and yet never actually arrive on
the character. The counter would climb, then quietly drop back down
on the next character load or game exit, with nothing ever granted.

**Root cause:** Only one piece of internal code was ever responsible
for turning a queued reward amount into an actual delivered grant —
and it lived inside the same kind of unreliable internal hook
described in the zone-transition crash fix above, one that doesn't
fire consistently on every PC setup. On setups where it didn't fire,
queued rewards just sat there, displayed but undelivered, until the
normal end-of-session cleanup zeroed the counters back out — silently
discarding them in the process.

**Fix:** Moved this logic into the same reliable, always-fires
internal hook that already handles the equivalent live-mode reward
path (and the custom boss / treasure cow systems), so queued
standalone-mode rewards are now delivered the moment they're queued,
on every setup, with nothing left to silently expire.

### Old character-save backup files were never being automatically cleaned up

**Symptom:** The mod periodically saves numbered backup copies of your
character's save file (named like
`CharacterName.d2s.20260608-153000.bak`) and is supposed to
automatically keep only the handful of most recent ones, deleting the
rest. In practice, none of them were ever being deleted — they simply
piled up in your save folder for as long as you played that character.

**Root cause:** A small internal bug in the cleanup routine caused it
to always compute an empty filename to search for, so it could never
actually find any of its own backup files to consider deleting — it
ran every time, found nothing matching, and quietly did nothing.

**Fix:** Corrected the internal logic so the cleanup routine now finds
its own backup files correctly and prunes them down to the intended
handful, as originally designed. (If you'd like to reclaim space from
backups that piled up before this fix, it's safe to manually delete
older `*.bak` files sitting next to your `.d2s` save — just leave a
few of the most recent ones in place as a safety net.)

### Defeating Baal on the "wrong" difficulty could end your entire run early and dump every check at once (Pulsar, Tall Sam)

**Symptom:** If your Archipelago goal was set to defeating Baal on a
specific difficulty — say, Hell — then defeating Baal on an *easier*
difficulty first (the normal play order almost everyone follows:
Normal, then Nightmare, then Hell) could incorrectly mark the entire
run as already complete. Every remaining check got released and
dumped all at once, far earlier than intended, with no way to undo it.

**Root cause:** The quest "Eve of Destruction" (defeat Baal) shares
the exact same internal quest number across Normal, Nightmare, and
Hell — the game only records "you defeated Baal," not which
difficulty you did it in. The mod's goal-completion check looked
solely at that shared quest number, so the very first time it saw a
Baal kill recorded — for virtually everyone, that's the Normal
playthrough, finished long before Hell — it treated a Hell-specific
(or Nightmare-specific) goal as already met.

**Fix:** The completion check now also compares the difficulty the
kill actually happened in against the difficulty your goal asks for,
so only a same-difficulty Baal kill can complete a difficulty-based
goal. (The same pass also caught — and closed — an identical,
not-yet-reported gap that left Collection- and Custom-goal characters
exposed to the same "early Baal ends everything" trap on their very
first ordinary Normal-Baal kill.)

### Manually editing your connection info or adding `ItemLevelReqs` to `d2arch.ini` got silently undone the next time you clicked Play (Congree, danRolleikon, JETgroovy)

**Symptom:** Editing `Archipelago/d2arch.ini` by hand — for example to
point the game at your own Archipelago server and slot name, or to
add an `ItemLevelReqs` line — seemed to take effect, but the very next
time you clicked "Play" in the launcher, the changes were gone without
a trace: connection info reverted back to a default test server/slot,
and any `ItemLevelReqs` line you'd added had simply vanished again.

**Root cause:** Before every "Play" click, the launcher quietly
re-checks your installation against the official file list and
silently re-downloads anything that doesn't match — by design, so a
partially-updated or corrupted install can heal itself without you
having to do anything. `d2arch.ini` is meant to be a file you
personalize, but it had been left off the launcher's "this one's
yours, don't touch it" list. The moment you changed so much as a
single character in it, its file size no longer matched what the
launcher expected — so it was quietly treated as "corrupted" and
silently replaced with the shipped template, overwriting your edits
with no warning that anything had happened.

**Fix:** Added `d2arch.ini` to the launcher's list of user-owned files
that the install check leaves alone — the same protection `d2gl.ini`,
`D2Hackmap.ini`, and other personal config files already had. Your
connection info and any settings you add to `d2arch.ini` now stick
across restarts and Play clicks. *(This fix lives in the launcher
itself, so you'll need the updated launcher — included in this
release — for it to take effect; updating the game files alone won't
do it.)*

### Three "Hunt" location names showed an old internal codename instead of the monster's real in-game name (Congree)

**Symptom:** Three "Hunt: …" location checks displayed a name that
didn't match what you'd actually see floating over the monster's head
when you found it — making them needlessly confusing to track down:

- "Hunt: Leatherarm" — the monster is actually **Creeping Feature**
- "Hunt: Web Mage" — the monster is actually **Sszark the Burning**
- "Hunt: Siege Boss" — the monster is actually **Shenk the Overseer**

**Root cause:** These three monsters carry old internal development
codenames left over in the game's data files, and those — rather than
the names the game actually displays on-screen — had ended up in the
location titles. The longer description text for each check was
already correct; only the short title shown in trackers and the AP
client was wrong.

**Fix:** Updated all three titles to match the monster's real in-game
display name, so what you see in your tracker or client is exactly
what you'll see when you find it.

---

## Behind the scenes — internal hardening from a full code review

While working through the bug list above, the underlying code for
several related systems got a deep, line-by-line review specifically
looking for similar latent issues — the kind that don't show up as a
specific player report, but are worth tightening up while already in
the neighbourhood:

- Removed a leftover duplicate check from game-library setup that
  could never actually accomplish anything (it retried the exact same
  lookup with the exact same inputs immediately after the first one
  failed — guaranteed to fail again the same way, every time).
- Added a couple of defensive checks around the in-game skill-page
  editor so it can no longer end up asking the game for information
  about "your character" during the brief moments when no character
  is actually loaded (e.g. while transitioning between screens) —
  closing off a theoretical crash that's never actually been reported,
  but that the surrounding code's pattern made possible.

Like the packaging changes below, neither of these changes anything
about how the mod behaves for you day to day — they're purely about
making the code itself sturdier.

---

## Behind the scenes — antivirus false-positive hardening

Marco's own antivirus occasionally flags `ap_bridge.exe` and/or the
launcher as suspicious — a well-known issue with "frozen" executables
(PyInstaller-built Python apps and self-contained single-file .NET
apps both have a structural shape that heuristic AV engines are
trained to eye warily). Two small, safe packaging changes that should
help at the margins:

- **Disabled UPX compression** in the bridge's PyInstaller build spec.
  UPX-packed executables are one of THE most common antivirus
  heuristic triggers — malware authors use the same compressor to
  obfuscate payloads, so AV engines specifically watch for its
  signature. (UPX wasn't even active in our actual build output, but
  the setting now correctly reflects — and guarantees — that.)
- **Added proper publisher/product info** to the launcher .exe
  (company, product name, description, copyright) in place of the
  blank fields it shipped with before. Executables with complete,
  coherent identity metadata read as more legitimate to heuristic
  scanners than ones with nothing filled in.

Neither change affects how anything behaves for you — it's pure
packaging hygiene, aimed at *reducing the odds* of a false alarm, not
guaranteeing one won't happen. The only fix that fully eliminates
"unknown publisher" warnings is signing releases with a paid
code-signing certificate, which costs real recurring money and isn't
something we're pursuing right now. If you do get a SmartScreen
prompt, "More info → Run anyway" remains the correct, safe response —
see the Install steps in past releases.

---

*Build artifacts will be listed at release time. Cycle started
2026-06-08 on top of Beta 1.9.12 baseline.*
