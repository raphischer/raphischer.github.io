# Personal Research Website

A lightweight GitHub Pages website for a researcher portfolio with automatic CV PDF generation.

## What this setup includes

- `index.html` + `styles.css` + `script.js` for a responsive static site
- `data/cv.json` for CV content (personal, statement, experience, education, etc.)
- `data/references.bib` for publication metadata
- `scripts/build_cv.py` to generate `CustomCoverletter.sty`, `cv.tex`, and `cv.pdf` from JSON and the website CSS palette
- GitHub Actions workflow to compile `cv.pdf` from `cv.tex`

## JSON structure

The `data/cv.json` follows this schema:

```json
{
  "personal": {
    "name": "Your Name",
    "role": "Your Position",
    "affiliation": "Institution Name",
    "birthinfo": "Date and Place",
    "nationality": "Your Nationality",
    "email": "email@example.com",
    "webpage": "https://yourdomain.com",
    "linkedin": "https://linkedin.com/in/profile",
    "scholar": "https://scholar.google.com/citations?user=...",
    "github": "https://github.com/profile",
    "picture": "picture.jpg"
  },
  "statement": [
    { "text": "Your research focus and background... " },
    { "text": "Linked phrase", "href": "https://example.com" },
    { "text": " and the rest of the statement." }
  ],
  "sections": [
    {
      "heading": "Professional Experience",
      "items": [
        {
          "period": "06/19 -- Today",
          "title": "Your Position",
          "organization": "Institution Name",
          "highlights": ["Bullet point 1", "Bullet point 2"]
        }
      ]
    }
  ]
}
```

## How to use

1. Update `data/cv.json` with your personal information, experience, education, and other sections.
2. For statement links that should appear on both the public website and in exported LaTeX/PDF, use the structured `statement` array with `{ "text": ..., "href": ... }` segments.
3. Add publications to `data/references.bib`.
4. Push to `main`; the workflow automatically generates `cv.pdf`, `cv.tex`, and `CustomCoverletter.sty`.
5. GitHub Pages serves the site from the repository root.

## Custom domain

Set your custom domain in `CNAME` and enable GitHub Pages in repository settings.

## Building locally

```bash
python scripts/build_cv.py --input data/cv.json --output cv.tex
```

This generates `cv.tex` and automatically compiles it to `cv.pdf` (requires `latexmk` or `pdflatex`).

To skip PDF compilation:

```bash
python scripts/build_cv.py --input data/cv.json --output cv.tex --no-compile
```

**First-time LaTeX setup:**

- **Windows:** Install [MiKTeX](https://miktex.org/) or [TeX Live](https://www.tug.org/texlive/)
- **macOS:** `brew install mactex`
- **Linux:** `sudo apt-get install texlive-latex-base texlive-latex-extra`

## Local testing

The site loads `data/cv.json` and `data/references.bib` with `fetch`, so it must be served over HTTP instead of opened directly from `file://`.

From the repository root, start a simple static server:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/` in your browser and verify the page renders, the CV content loads, and the publication list appears.

If `python` is not available on your system, use the equivalent command for your local Python launcher, such as `py -m http.server 8000` on Windows.

If the page is still empty, make sure the server is serving this repository root and not a different folder. On Windows, you can force that explicitly with:

```bash
py -m http.server 8000 --directory d:\Repos\raphischer.github.io
```

You can also open the browser DevTools console and confirm that `data/cv.json` and `data/references.bib` return `200` instead of `404`.
