# PDFsnip

A free, open-source, **100% client-side** PDF toolkit. Eight PDF tools that run entirely in your browser — your files never leave your device.

🔗 **Live demo:** [madebybalaji.com/pdfsnip](https://madebybalaji.com/pdfsnip/)

## ✨ Features

- ✂️ **Split PDF** — Extract any pages, reorder, rotate, or delete visually before downloading
- 🔗 **Merge PDFs** — Combine multiple PDFs into one, drag to reorder
- 🗜️ **Compress PDF** — Shrink PDFs by up to 80% with three quality levels
- 🖼️ **PDF → Images** — Export every page as PNG or JPEG up to 216 DPI
- 🔏 **Watermark** — Stamp text on every page with custom opacity, position, and color
- 🔢 **Page Numbers** — Add configurable page numbers in any position and format
- 🔒 **Password Protect** — AES-128 encrypt your PDFs in one click
- 🔓 **Unlock PDF** — Remove the password from any PDF you own

## 🛡️ Privacy by design

This is a **single static HTML file**. There is no server, no upload, no telemetry, no tracking, no analytics. Every PDF you process is handled locally by JavaScript running in your own browser tab. Close the tab and it's gone.

## 🚀 Run it

### Option 1 — Open the file
Just open `index.html` in any modern browser. That's it.

### Option 2 — Local server (optional)
```bash
python -m http.server 8000
# then open http://localhost:8000
```

### Option 3 — Deploy
Drop the folder onto any static host:
- [Netlify](https://app.netlify.com/drop) — drag and drop, done
- [Cloudflare Pages](https://pages.cloudflare.com/) — connect this repo
- [GitHub Pages](https://pages.github.com/) — enable in repo settings
- Vercel, Surge, S3, or your own nginx — anything that serves static files

A `netlify.toml` is included with sensible security headers (CSP, X-Frame-Options, nosniff, Referrer-Policy).

## 🛠️ Tech stack

- **HTML / CSS / Vanilla JS** — no framework, no build step
- **[pdf-lib](https://pdf-lib.js.org/)** — PDF reading, writing, and manipulation
- **[JSZip](https://stuk.github.io/jszip/)** — building ZIP downloads
- **[download.js](http://danml.com/download.html)** — triggering file downloads

That's the entire stack. No npm, no bundler, no node_modules.

## 📁 Project structure

```
pdf-splitter/
├── index.html       # The entire app
├── netlify.toml     # Static hosting config + security headers
├── tests.md         # Manual test plan
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## 🤝 Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

Quick version:
1. Fork and branch from `master`
2. Edit `index.html` directly
3. Test by opening it in a browser
4. Open a PR with a clear description

## 📜 License

MIT — see [LICENSE](LICENSE). Use it, fork it, host it, do whatever.
