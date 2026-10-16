# Tuition ep. 02: "I gave myself one hour to build an AI video editor" — design

## Brief

- **Speaker:** Saagii, one talking-head take to camera (`raw/58E1AF89-….MP4`, 1080x1920, 30 fps,
  SDR BT.709, 101.6 s), holding a mic. Light grey wall behind him.
- **What it is:** episode 2 of his series "making my tuition by January 15th". He gave himself one hour
  to build an AI video editor; it took five hours for v1; this video was edited by it.
- **Audience:** people scrolling Reels/Shorts/TikTok who follow build-in-public / AI content.
- **Format:** 1080x1920, 30 fps, −16 LUFS, true peak ≤ −1.5 dBTP.
- **Saagii's direction (this session):** "use the brand guideline for the motion graphics and have fun with
  it" + "more tech vibe like cyberpunk so the colors really pop through on the black background of the
  motion graphics."
- **Brand source:** Figma `Studio_21` → page "Studio 21 Brand - neutral" (node 209:49), brand sheet frame
  210:2 ("draft for approval · Oct 2026"). Logos exported from components 244:77 (Monogram B violet) and
  244:68 (Wordmark A dark); background rects stripped, geometry untouched.

## Style prompt

Cyberpunk build-terminal on black. The graphics panel is Graphite pushed toward black at the edges, with
the brand's two accents used as **neon light**: Signal Violet for glows, rails, chips and the seam;
Mint for live HUD readouts, check marks and highlighted words. Space Grotesk Bold numbers and
headlines with a violet/mint chromatic split (RGB-offset in brand colours, not red/blue). Inter Semi Bold
caps labels like `// 02 · ANALYZE`. Texture: fine scanlines, a receding violet perspective grid, and HUD
corner brackets. Motion is snappy: flicker-on entrances, a short slice-glitch at major beat changes,
type-on readouts, scrambling digits. Saagii stays on screen the whole time (split, face or punch-in).

## How the brand rules were applied (and where the brief pushed on them)

| Brand rule (Figma "Usage") | What this edit does |
| --- | --- |
| Palette: Graphite, Slate, Mist, Cloud, White, Signal Violet, Lilac, Mint | Only these. "Black" = Graphite `#15171C` with a radial falloff to `#0A0B0E` (a darker shade of Graphite) for the neon-on-black look Saagii asked for. No new hues. |
| Fonts: Space Grotesk + Inter only | Space Grotesk 700/500 for numbers, headlines, captions; Inter 600 caps (8 % tracking) for labels. No mono font, even though cyberpunk usually wants one. |
| One accent per slide on text: Violet OR Mint | Text accent is **Mint** (on Graphite, 10.06:1). Violet appears as light/fill: glows, chips (White text on Violet, 6.23:1), seam, grid. |
| No Mint text on Violet / Cloud / White | Mint text only sits on Graphite/black. Mint on Violet appears only as the monogram's own typing dots (decor). |
| No robots, glowing brains, circuit boards, green-on-black code | Cyberpunk feel comes from neon glow, HUD frames, scanlines, glitch and grid. No code rain, no circuit traces, no robot/brain imagery. |
| No invented results, stats, testimonials | Every number on screen is real: 1 hour limit, 30 min–1 hr per edit, 5 hours (all spoken); raw 1:41 → cut 0:46, 249 raw words, 26 kept ranges (measured from this edit's own files). |
| Write "Studio 21" | The Studio 21 marks are **not** placed on this video: it's Saagii's personal series (Drive folder `saagii_so`), not a Studio 21 client piece. Only the look is borrowed. Open question for Saagii. |

## Colours

| Token | Hex | Role here |
| --- | --- | --- |
| Graphite | `#15171C` | Graphics canvas, caption box |
| Ink (Graphite, darkened) | `#0A0B0E` | Vignette edges of the canvas only |
| Slate | `#4B5262` | Dim HUD lines, removed waveform bars, struck values |
| Mist | `#E4E7EE` | Secondary text on dark |
| Cloud | `#F5F6F8` | Headlines, caption text |
| Signal Violet | `#5440F0` | Neon light: glow, seam, grid, rails, chips |
| Lilac | `#DDD8FF` | Caption box edge, light on violet |
| Mint | `#3FD9B2` | Live readouts, highlighted caption words, checks |

## Typography

- **Space Grotesk** 700 (numbers, headlines, captions) / 500 (subheads). Local `assets/fonts/space-grotesk-latin-var.woff2` (Google Fonts, OFL).
- **Inter** 600 caps, letter-spacing 0.08 em (HUD labels). Local `assets/fonts/inter-latin-var.woff2` (Google Fonts, OFL).

## Captions

- 1–3 words per chunk, phrase boundaries, hard swap, on screen 2 frames before the first word, never
  before the previous chunk's last word ends.
- One look for the whole reel: Space Grotesk Bold uppercase ~76 px, Cloud on a Graphite box (92 %) with a
  Lilac 2 px edge and a violet neon glow. Box corners follow the brand bubble (one sharp corner,
  bottom-left).
- Mint (with a soft mint glow) on 25–40 % of chunks: the concept or the payoff ("AI video editor",
  "five hours", "edited by this editor"). No second text accent.
- Position: on the seam in split, on the chest in face, lower chest in punch-in. Never over the mouth or chin
  (face measured: hair top ≈ y 420, mouth ≈ y 1010, chin ≈ y 1125 in source pixels).

## Layouts

- **split:** graphics panel on top (y 0–880), Saagii below, shifted down 540 px so his face sits in the
  lower panel (mouth ≈ y 1550).
- **face:** Saagii full frame, scanline + corner-bracket overlay.
- **punch:** Saagii at 1.3× around the face for conviction lines.

## The main object and the open loop

One persistent object: the **build timer**.

- Planted 0:00–0:03: "I gave myself one hour…": a HUD timer reading `1:00:00 LIMIT` flickers on and starts
  counting down.
- Reminder ~0:08–0:12: "it took quite a lot of time, which I will tell you in the end": the timer comes
  back with its digits scrambling, stamped `ACTUAL BUILD TIME · REVEALED AT THE END`.
- Closed ~0:30: "And it took me five hours": the scramble resolves to `5:00:00`, the `1:00:00` limit is
  struck through, and an overtime bar runs to 5×.

A second, smaller object carries the middle: the **raw-footage monitor**. In the pipeline beat it receives
Saagii's real raw take, gets scanned ("AI analyzes it"), its real waveform loses its dead space ("cuts the
dead spaces": 1:41 → 0:46), gets a caption, gets a B-roll panel on top, renders an export bar, gets a
music EQ, and becomes a posted card. The meta line ("the video you're watching right now is edited by
this editor") calls back to it: the whole reel gets the monitor's HUD frame and a strip of *this* video's
real cut list with a moving playhead.

## Three openings considered (same truthful speech)

1. **Challenge first (selected):** "I gave myself one hour to build an AI video editor" over the timer
   flickering on at `1:00:00` and starting to count down, with a violet `AI VIDEO EDITOR` target chip.
   Topic and stake are clear in one line; by 0:03 the timer is visibly running. Payoff: the timer closes at
   "five hours".
2. **Meta first:** open on "the video you're watching right now is edited by this editor" (moved from
   0:89), with the HUD frame around the reel. Strong curiosity, but "this editor" has no referent for the
   first 2.5 s and the end loses its reveal.
3. **Result first:** open on "it took me five hours to build…". Kills the loop Saagii set up himself
   ("I'll tell you at the end"), so the middle has no reason to be watched.

**Why 1:** clearest topic in the first second, a stake the viewer can root for, a visible change by second
3 (the timer runs), and the loop is Saagii's own words. Only concept 1 is built; 2 and 3 are written
comparisons, not rendered animatics.

## Sound

- Voice only, cleaned and levelled. **No music**: no licensed track was supplied. (Saagii says "put some
  background music on it" in the video; the edit shows an EQ graphic there but plays no music. Offer a
  track in the next round.)
- Sparse SFX on visible actions only: soft data ticks when the timer flickers on, a dry click per
  pipeline node, a short filtered glitch burst on the two big glitch transitions, a low damped thump when
  `5:00:00` lands, a soft two-note tone on POSTED and WIN. No lasers, no zaps, no whoosh on every cut.

## What NOT to do

- No fonts or colours outside the brand sheet; no Mint text on Violet/Cloud/White.
- No code rain, circuit boards, robots or glowing brains.
- No invented numbers. No logos of other products (no editing-app or platform logos).
- No captions over the mouth/chin; no white text on the light wall without the box.
- No full-frame flashes; glitches are slices over the panel, ≤ 4 frames.
- Don't show or play the removed swear (raw 26.1 s). The raw-monitor footage is muted and avoids that range.
