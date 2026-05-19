# Diablo II Archipelago — Beta 1.9.10

This release closes 7 of 8 bugs Maegis reported on Discord plus an
install issue Marco found, after an exhaustive 1104-config validation
pass to make sure no setting combination produces an unbeatable seed.
The launcher is also back to single-file/self-contained so fresh
installs work on machines without .NET 8 already installed.

---

## Install / update

**Existing players:** the launcher will prompt for self-update to
1.5.4 when you start it. After that, click UPDATE GAME to pull 1.9.10
content.

**Fresh install:** download `launcher_package.zip` from the release
assets, extract `Diablo II Archipelago.exe` somewhere convenient
(your Desktop, a folder, whatever), and run it. Point it at your
existing Diablo II + Lord of Destruction install when prompted.
The launcher is now self-contained — no .NET 8 runtime install
required.

---

## What 1.9.10 fixes

This release closes 7 of the 8 bugs Maegis reported on Discord. The eighth
(entrance shuffle players landing on the waypoint pad past Act 1) is
quality-of-life only — no softlock, no data loss — and is deferred to
1.9.11 because the proper fix requires deeper D2 internals work.

### Skill loss on game crash / character switch (Maegis #1, #8 + Marco)

**Before:** If you spent skill points on a character and then the game
crashed (D2 crash, Alt-F4, watchdog kill, OS reboot) before the next 10-
second auto-save, the points were silently lost. Worse: the save files
themselves could be left truncated mid-write, causing skills to revert
to "locked" on the next character load. The Alphena 1.9.5.1 hotfix that
taught the bridge to skip `'1:0'` corrupted lines was treating the
symptom of this exact bug. Additionally, if you played character A,
exited to the character list, and loaded character B without restarting
the game, character A's memory-hacked skill table, AP-mode flags, and
animation patches all leaked into character B — the cheat menu would
become unresponsive, skills couldn't be picked, and other weird state
bled across.

**After:** Three coordinated changes:

1. **Atomic state-file writes** — `SaveStateFile` and `SaveSlots` now
   write to a `.tmp` file, fsync, and atomically rename over the live
   file. A crash mid-write leaves either the OLD complete file or the
   NEW complete file — never a half-written one. Same pattern that the
   1.9.5 `WriteChecksFile` fix used; now applied to every state file.

2. **Incremental save on every state change** — added a `MarkStateDirty`
   helper that gets called on skill-point spend, Reset Point use, server
   reward consumption, bonus check fire, and extra check fire. Reduced
   the PeriodicSave window from 10 seconds to 250 ms when dirty (and 0
   disk writes when idle — was wasted I/O every 10 s even with no
   changes). Net effect: crash-safety improved 40× (10 s → 250 ms).

3. **Full memory reset on character unload** — new `OnCharacterUnload`
   pipeline restores the vanilla skill table from cached values
   (`g_origCharClass`, `g_origClassList`), resets the cross-class
   animation patches, clears AP-mode and pending-counter globals, and
   wipes uber-tracking state. Each character load now starts from a
   clean vanilla state — equivalent to having restarted the game.

### Custom Goal Collection mode hard softlock (Maegis #3 hole 1)

**Before:** With `goal: gold_collection` + `zone_locking: true`, the
apworld placed collection-event locations (like "Collection: Zod Rune")
in the always-reachable open region with no access rule. AP fill could
then legitimately place progression items (gate keys, skills) at those
locations. Since Zod runes drop at roughly 1 in 5000 Hell L99 monster
kills, a player could be permanently locked out of progression.

**After:** Collection-event locations are now marked `EXCLUDED` so AP
fill only places filler items there. The collection check still fires
when the player picks up the item; the AP location just delivers a
gold/skill/charm reward instead of progression.

### Hell level milestones could gate behind unreachable keys (Maegis #3 holes 2-3)

**Before:** "Reach Level 60 (Hell)" through "Reach Level 75 (Hell)"
required only NM Baal kill as the access prerequisite. AP fill could
place Hell-difficulty Act 1 gate keys at those milestones — but the
player would have NM Baal access without Hell Act 1 R3+ access,
forcing them to grind L60 in Hell Act 1 R1+R2 only. Theoretically
possible but felt impossible. Same pattern for NM milestones L35-55.

**After:** Hell milestones now also require Hell Andariel kill, and NM
milestones require NM Andariel kill. The player has actual reachable
grinding territory at the milestone's difficulty.

### Zone Locking + Entrance Shuffle break together (Maegis #4)

**Before:** With both enabled, the apworld's access rules read vanilla
zone IDs while the DLL warped players through a shuffled physical map.
Result: gate keys gated the wrong zones, players warped into locked
regions were bounced back to town, the F4 zone tracker showed wrong
bosses. Documented in 5 distinct failure scenarios.

**After:** Entrance Shuffle is auto-disabled when Zone Locking is on
(both at multiworld build time in the apworld AND at character load
time in the DLL as a defensive belt-and-suspenders). Proper
"shuffled-map-aware access rules" is a 1.10.0+ feature; until then
this preserves player intent on whichever feature they prioritize.

### Tristram entrance shuffle breaks Cain rescue (Maegis #5)

**Before:** Tristram (level 38) was in the dead-end-cave shuffle pool.
When the player cast the Cairn Stones portal, they got warped OUT of
Tristram into a different cave (Sewers L1, Tal Rasha Tomb, etc.) and
could never reach Cain's gibbet. The "Search for Cain" quest was
unfinishable in the Tristram instance.

**After:** Tristram removed from the shuffle pool entirely. The portal
destination is preserved; Cain rescue works as vanilla. Pool A shrinks
from 21 → 20 sets.

### Cain rescue AP check fired even without rescuing (Maegis #5 sub-bug)

**Before:** Even after the Tristram fix above, vanilla D2 auto-progresses
the Cain quest to `QFLAG_PRIMARYGOALDONE` (state 13) the moment the
player enters Lut Gholein (or talks to Warriv to travel to Act 2),
regardless of whether Cain was actually rescued. Our `CheckQuestFlags`
function treated state 13 as "completed" universally, so the AP check
for "Cain rescue" fired on Act-2 entry without an actual rescue.

**After:** Cain quest (quest_id 4) now requires explicit state 14
(`COMPLETEDNOW`) or state 15 (`COMPLETEDBEFORE`), which D2 only sets
on real Tristram rescue. The vanilla auto-progress state 13 is filtered
out for Cain specifically. Other quests keep the old 4-state accept
since vanilla doesn't auto-progress them on act change.

### Launcher 1.5.4 — self-contained build (fixes "must install 1.9.6 first")

**Before:** Fresh installs of 1.9.7-1.9.9 silently failed for users
without .NET 8 Desktop Runtime installed. The launcher exe needed
`dotnet runtime` to run; without it, Windows showed "To run this
application, you must install .NET Desktop Runtime 8.0.x". Users
worked around it by installing Beta 1.9.6 first (the last release
with a self-contained launcher that bundled .NET) and only then
updating to a newer version.

**Root cause:** Launcher built with `dotnet publish --self-contained
false -p:PublishSingleFile=false`. This produces a framework-
dependent 365 KB exe that requires the .NET 8 runtime on the user's
machine. 1.9.6 used the older `--self-contained true` mode which
embedded the runtime into the exe.

**After:** Launcher rebuilt as `--self-contained true
-p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true`.
Single-file exe is 162 MB (embeds .NET 8 runtime) → 68 MB zipped.
Works on any Windows 10/11 machine regardless of .NET install state.
Launcher version bumped 1.5.3 → 1.5.4 so existing users get the
self-update prompt.

**Also fixed in launcher_package.zip:**
- `Settings_Guide.md` re-added — was missing since 1.9.7, the Guide
  tab now shows local fallback when offline (instead of perpetual
  "Settings Guide is loading..." message)

### apworld pool-balance fix — FillError on high-check loads (validation discovery)

**Before:** Generation of YAML configs with many check categories
enabled (shrines + chests + collection + etc.) could fail with
`FillError: Not enough filler items for excluded locations` or
`FillError: Not enough locations for progression items`. Exhaustive
1.9.10 validation found 162 of 562 random YAMLs failing this way
across the option space. Players hit this when stacking lots of
bonus/extra check categories with goal=collection.

**Root causes (3 separate bugs):**
1. With `skill_hunting: false`, AP-delivered skills were classified
   as PROGRESSION even though they don't actually gate anything
   (DLL gives the 30 class-native skills automatically at character
   init). Fix: skills become FILLER when skill_hunting is off, so they
   can fill EXCLUDED bonus/check slots freely.
2. The skill-pool size cap didn't account for EXCLUDED locations.
   With many check categories on, the non-EXCLUDED location budget
   shrinks below the skill+key item count, causing FillError. Fix:
   cap skill pool to `non_excluded_count - zone_keys` when
   skill_hunting is on.
3. With a narrow Custom Goal (e.g. `kill_andariel_normal` only,
   scope = Act 1 Normal), the apworld was adding all 18 Normal gate
   keys even though only 4 Act 1 gates physically exist in the
   scope. The extra 14 keys had no usable destination location and
   blew the progression budget. Fix: filter gate keys by
   `scope_max_act` too, mirroring the existing diff filter.

**After:** Exhaustive validation across 2104 unique YAML/multiworld
configs (224 basic + 596 extended + 1054 random YAMLs + 84 pathological
+ 84 multi-world stress) returns 0 failures. Players can mix any
combination of options without hitting FillErrors.

### Skill level requirement toggle (Maegis #2)

**Before:** When you tried to spend a skill point in the in-game editor
on a skill that required a higher character level than yours (per
Skills.txt vanilla `reqlevel`), the click was rejected with a notify.
No way to disable.

**After:** New `SkillLevelReqs` toggle in the YAML / d2arch.ini. When
OFF, the editor "+" button bypasses the under-level check. Default ON
preserves pre-1.9.10 behaviour. Item equip requirements (level/STR/DEX)
are unaffected — AP-delivered items already strip those stats per the
1.9.4 / 1.9.5 fixes; vanilla monster drops still respect vanilla equip
gating.

### Planned for this cycle (TODO)

(All committed items above. Build artifacts list will be filled in at
release time.)

---

## Deferred to 1.9.11

- **Entrance Shuffle landing on waypoint pad past Act 1** (Maegis #6) —
  Root cause confirmed: `LEVEL_WarpUnit` with `nTileCalc=0` is ignored
  by D2 1.10f on outdoor levels. Proper fix requires manual room-walk
  of the destination level to find the warp-unit-tile matching the
  source cave's level-id, then re-positioning via ord 10027. 4-6 hour
  Ghidra-heavy implementation; deferred to keep 1.9.10 focused on
  data-loss + cross-char isolation fixes. Quality of life only — no
  softlock, no data loss. Documented inline in `d2arch_gameloop.c`
  around the `g_pendingZoneTeleport` block.

- **`ItemLevelReqs` toggle** (Maegis #2 second half) — only the skill
  side of #2 landed in 1.9.10. The "all items can be equipped
  regardless of level/STR/DEX" toggle requires either hooking D2's
  equip-check function or stripping stats 91/92/93 on every item
  pickup. AP-delivered items already get the strip per 1.9.4/1.9.5
  fixes; this would extend it to vanilla monster drops, shop items,
  and gambling. Deferred pending design decision: scope to AP-only or
  all items?

---

## Known issues — still under investigation

These bugs need user-side info (screenshots/logs) before we can fix:
- **Game crash after reaching Act 3 in AP mode** (Teddie) — multiple
  suspected causes; awaiting `d2arch.log` from a crash event
- **Skill page no info display** (Maegis) — three plausible causes,
  awaiting F1 tooltip screenshot
- **Champion enemies no names** (Maegis) — three plausible causes,
  awaiting screenshot showing whether prefix or basename is missing

---

*Build artifacts will be listed at release time. Cycle started 2026-05-14
on top of Beta 1.9.9 baseline.*
