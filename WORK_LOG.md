# Travel Quiz Work Log

## Current state

- `index.html` is the ten-choice travel photo quiz. It loads `travel-data.js` and `travel-photos.js`.
- The page filters its question pool to places with a photo mapping, shuffles those places without ranking bands, and shows the full-dataset visitor rank after the answer.
- Scoring uses a 15-second timer and streak-times-whole-seconds. The all-time top ten is stored in the browser.
- Current inventory: 783 image mappings and 783 corresponding local files under `images/`; `places-without-photos.csv` has 286 no-photo entries.
- The original `gerber-landmarks.csv` has 1,075 attraction records. The 783 photo mappings plus 286 no-photo records account for 1,069; reconcile the remaining six before claiming complete classification.

## Decisions from the conversation

- The user chose 1,000 global attractions ranked by visitor popularity after being told official U.S. travel data ranks countries, not individual attractions.
- The user later said not to bin by rank: questions can come from the attractions in any order, and after the answer the app should show each attraction’s rank.
- Representative images should come from Wikipedia/Wikimedia and be downloaded into the project so the quiz does not need to find a picture on each load.
- The user reported that the quiz initially showed neither a picture nor choices. The final requested behavior was to use only questions with a picture in the local image folder.
- The user created a separate GitHub repository for travel and asked where the image folder should go; keep `images/` beside `index.html` and its JavaScript data files when publishing.

## Known mismatch / follow-up

- `travel/README.md` currently says the quiz searches Wikipedia at question time and caches links in the browser. That statement is stale: `index.html` uses the local `TRAVEL_PHOTOS` map and filters the question pool to saved-photo entries. Update the README if requested.
- The source-data, mapped-photo, and no-photo counts leave several entries unaccounted for. Check names against the source before expanding or promising full coverage.
- Preserve source and license credits without using answer-revealing image filenames or captions in the question view.

## Latest change

- The source link now uses generic “View photo source” text rather than exposing the source page or image filename. The link and all photographer/license attribution are hidden during a question and shown after the answer or timeout.
- If a saved image fails to load, the quiz removes that destination from the current question pool and skips to another one. It reports when fewer than ten working photos remain.
