# Arson Wraps pitch reel — design

## Brief

- **Speaker:** Saagii, talking to camera (two iPhone takes, IMG_4780 + IMG_4781).
- **What it is:** a 9:16 short-form pitch. Saagii cold-called a Calgary wrap shop
  (Arson Wraps), built an AI "upload your car, see it wrapped" feature into their
  site, and offers the same thinking to other businesses.
- **Audience:** small-business owners scrolling Reels/Shorts/TikTok.
- **Intended action:** "if you want the same for your business, hit me up."
- **Formats:** 1080x1920, 30 fps. No 16:9 version requested.
- **Motion-graphics source:** screen recording of the real Arson Wraps site
  (`raw/screen-recording.mov`, 2940x1912 @ 60 fps, no audio).

## Style prompt

Dark asphalt canvas with hot magenta and lime-green heat, taken directly from the
Arson Wraps brand sheet and the live site. Condensed uppercase Anton headlines,
Inter for small labels. The site itself is the hero: real UI, real before/after,
cropped tight so it reads on a phone. Graphics are minimal, confident, and land
on the spoken word. Every change between layouts is a hard cut (reel house style);
movement comes from slow push-ins on footage and purposeful wipes, not decoration.

## Colors (from the Arson Wraps brand sheet)

| Token | Hex | Role |
| --- | --- | --- |
| Asphalt Black | `#0B0B0D` | Canvas, caption box fill |
| Gunmetal | `#1A1A1F` | Surfaces, cards |
| Arson Magenta | `#E41395` | Primary emphasis (concept / key word) |
| Lime Burn | `#35D430` | Payoff / action / "after" |
| Ignition Orange | `#FF4D1A` | The wrong way / negation |
| Smoke White | `#F5F5F7` | Caption and headline text |
| Ash Grey | `#9A9AA5` | Muted labels |

## Typography

- **Anton** (400), uppercase, for captions and headlines. Local file
  `assets/fonts/anton-latin.woff2` (Google Fonts, OFL).
- **Inter** (500–800) for chips and small labels. Local file
  `assets/fonts/inter-latin-var.woff2` (Google Fonts, OFL).

## Captions

- 1–3 words per chunk, split on phrase boundaries, hard swap, shown 2 frames before
  the first word.
- One look for the whole reel: Anton uppercase ~84 px, Smoke White in an Asphalt
  box (88 %) with a thin light edge so it reads on the dark site and on the room.
- Whole-chunk color on 25–45 % of chunks: magenta = the concept, lime = the
  payoff/action, orange = the wrong way ("not about colors").
- Position: on the seam in split layouts (y ≈ 880), on the chest in face layouts.
  Never over the mouth or chin.
- Whisper mis-hearings corrected in captions only where the audio is clear:
  "cold cuddling" → "cold calling", "cd end result" → "see the end result".

## Layouts

- **split:** site footage on top (y 0–880), Saagii below (y 880–1920).
- **face:** Saagii full frame.
- **punch:** Saagii at ~1.28× on the face for conviction lines and the CTA.
- **graphic:** brand cards on the top panel (still split, Saagii stays visible).

Saagii is on screen for the whole reel (split or face), so the "never gone more
than 3.5 s" rule holds automatically.

## Three openings considered (same truthful speech)

1. **Chronological thesis:** start on "When it comes to businesses having a
   website, it's not about colors…" over the site hero. Clear, but a generic
   claim; nothing visibly changes by second 3, and "it's not about colors" over a
   wrap shop needs context the viewer doesn't have yet.
2. **Cold-open question (selected):** start on "If these people are going in to
   change the color of the car, why not do it before they come in?" The top panel
   shows the uploaded white GR86, and on "change the color" a lime wipe turns it
   green (the site's real before/after output). By second 3 the viewer has seen the
   transformation and heard the question. Payoff: the real slider demo at ~0:35.
3. **Build-first:** start on "So I built this custom AI component into their
   website" over the upload UI. Strong for developers, weaker for business owners:
   it shows a tool before giving a reason to care.

**Why 2:** it's the only opening with a visible state change by second 3, it works
muted (white car → green car), and the question opens a loop the demo closes.
The line is moved from 0:36 in the raw take; the sentence it introduces ("So I
built…") still follows the story logically without it.

Only concept 2 was built and rendered in this draft; 1 and 3 are written
comparisons, not rendered animatics.

## Open loop

- Planted 0:00–0:05: "why not do it before they come in?" + the white→green glimpse.
- Reminded 0:26–0:34: the upload UI and picking Lime Green.
- Closed 0:34–0:41: "the AI does its magic and spits out an image of their car
  being wrapped in that color" over the real loader and the real before/after slider.

## Sound

- Voice only, normalized. No music bed in this draft (no licensed track is
  available in the project; the two music files in other kit projects belong to
  those projects). Offer music in the next round.
- Sparse, soft SFX only on visible actions: an air whoosh on the hook wipe, dry
  clicks on UI selections, a dry stop on each "not about" strike, a damped tap when
  the end card lands. No whoosh on every cut.

## What NOT to do

- No invented results, numbers, or extra AI outputs: the only real AI output in
  the recording is the Lime Green GR86, so that's the only "after" shown.
- No personal data: the quote form at 1:18–1:32 of the screen recording shows a
  real name, phone and email. It's excluded.
- No macOS menu bar, file picker, or desktop sidebar on screen (cropped / avoided).
- No white text on light backgrounds; no captions over the mouth.
- No logo redraws: the Arson Wraps mark appears only as captured in the site.
