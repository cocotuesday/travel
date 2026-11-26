# Travel Quiz Project Notes

These instructions apply only to the travel-landmark quiz in this folder.

## Data and local photos

- `index.html` loads `travel-data.js` and `travel-photos.js`.
- The question pool must include only places with a mapping in `TRAVEL_PHOTOS` to a saved local image. Keep each mapped image in `images/`; do not add a live Wikipedia/Wikimedia lookup fallback unless the user asks.
- Preserve the source/credit link for each image. Do not use a source filename or caption that gives away the answer before the player answers.
- Keep source links and all attribution hidden during an active question so neither titles nor credits can reveal the answer. Show them only after the answer or timeout; never display `sourceTitle`.
- If a mapped local image fails to load, remove that place from the active pool and draw another question. Keep ten choices available when at least ten working photos remain.
- `gerber-landmarks.csv` is the original attraction list; `travel-data.js` is what the page loads. The CSV is not loaded directly by the browser.
- `places-without-photos.csv` records places for which no usable photo was saved.

## Preserve the requested game rules

- Use ten multiple-choice answers and a 15-second timer.
- Correct-answer score is the current streak value multiplied by whole seconds remaining.
- Select places in random order across the available photo-backed pool; do not reintroduce ranking bins.
- Show the place’s visitor-count rank after the answer, based on its position in the full dataset.
- Keep the all-time top ten local to the current browser/device unless the user asks for shared scores.

## Work with the user

- The user asked that the quiz use downloaded images so it does not depend on finding an image during play, and then clarified that questions without a local image should be excluded.
- The user prefers incremental work. Preserve the existing quiz behavior when making a focused change, and flag any mismatch between the README and actual code before relying on it.
