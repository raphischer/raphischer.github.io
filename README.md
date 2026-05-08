# Personal Research Website

A lightweight GitHub Pages website for a researcher portfolio with automatic CV PDF generation.

## What this setup includes

- `index.html` + `styles.css` + `script.js` for a responsive static site
- `data/cv.json` for CV content (personal, statement, experience, education, etc.)
- `publications/references.bib` for publication metadata
- `scripts/build_cv.py` to generate `cv.tex` from JSON (matches your LaTeX template)
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
  "statement": "Your research focus and background...",
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
2. Add publications to `publications/references.bib`.
3. Push to `main`; the workflow automatically generates `cv.pdf` and `cv.tex`.
4. GitHub Pages serves the site from the repository root.

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

