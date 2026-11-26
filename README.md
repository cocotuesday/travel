# Where in the World?

A mobile-friendly, ten-choice travel photo quiz. Open `index.html` in a browser while connected to the internet. `travel-data.js` contains the landmark list; `gerber-landmarks.csv` is the original source file.

Each run shuffles the entire landmark list and selects questions without ranking bands. The visitor counts are used only to show a place's rank after the answer. Each correct answer earns the current streak number multiplied by the whole seconds left on the 15-second timer. A wrong answer or timeout ends the run. The all-time top ten is stored in that browser on that device.

The quiz searches Wikipedia for a representative photo as each question appears and caches found image links in the browser. Keep `index.html` and `travel-data.js` together when copying or publishing the app. The CSV is included for editing the source list, but the quiz does not load it directly.

To publish this folder in a GitHub Pages repository, upload the files in this folder together. If the folder is named `travel` at the repository root, the page is available at `https://USERNAME.github.io/REPOSITORY/travel/` once GitHub Pages is enabled.
