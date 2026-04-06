# PDF Studio – Test Plan & Test Cases

> Generated: 2026-04-03
> Source reviewed: `netlify/index.html`
> Tools used: pdf-lib 1.17.1 (Web Worker), pdf.js 3.11.174, JSZip

---

## Scope

Features **implemented** in this build:
- Split PDF (with page thumbnails, selection, rotate, delete, reorder)
- Merge PDF (multi-file, drag-to-reorder)
- Dark / Light mode toggle (persisted in localStorage)
- File upload validation (type, size)
- Download options: ZIP all, ZIP selected, single page, range ZIP
- Page management: select, rotate, delete, restore, drag-reorder

Features **not yet implemented** in this build (no UI or JS found):
- Compress, Watermark, Page Numbers, PDF to Images, Extract Images, Password Protect, Unlock PDF

---

## Bug / Code Issue Report

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| B1 | High | `addMergeFiles()` L1481–L1497 | Corrupt / renamed non-PDF files are pushed into state even when `pdfjsLib.getDocument()` throws — the `catch` block only sets `pageCount = '?'` and continues, so garbage files silently enter the merge queue. |
| B2 | Medium | `loadSplitFile()` L1049–1056 | Validation only checks extension and MIME type; a file renamed to `.pdf` but containing non-PDF bytes passes, then fails later during processing with a raw worker error rather than a friendly message. |
| B3 | Medium | `loadSplitFile()` L1049–1063 vs `clearSplitFile()` L1066–1080 | Loading a *replacement* file hides the results panel but does **not** clear `state.pageBuffers`, `state.pageOrder`, `state.rotations`, or the split badge. If the user cancels midway the stale state remains. |
| B4 | Medium | `downloadRange()` L1432–1442 | Range filter uses original page indices (`i + 1`) compared to `rangeFrom/rangeTo`. After reordering or deleting pages the displayed page numbers diverge from the filter values, so the downloaded range may not match what the user sees. |
| B5 | Medium | `startSplit()` L1112–1131 & `startMerge()` L1574–1591 | `worker.terminate()` and `URL.revokeObjectURL()` are only called on the **success** path. A processing error leaks the Web Worker and the blob URL. |
| B6 | Low–Medium | `renderMergeList()` L1511–1525 & `showToast()` L1654–1660 | Filenames and error messages are injected via `innerHTML` without sanitisation. A file named `<img src=x onerror=alert(1)>.pdf` would execute arbitrary JS. Use `textContent` or escape HTML entities. |
| B7 | Low | `setBusy()` L1644–1646 | Only disables the **Split** button. During ZIP creation (`buildAndDownloadZip`) the delete, rotate, and reorder controls remain active, allowing state mutation while a download is in progress. |

---

## Test Cases

### 1 – Split PDF

| ID | Title | Steps | Expected Result |
|----|-------|--------|-----------------|
| S01 | Valid PDF upload via file picker | Click "Choose File", select a valid `.pdf` | File info bar shows filename and size; "Split PDF" button enabled |
| S02 | Valid PDF upload via drag-and-drop | Drag a valid `.pdf` onto the split drop zone | Same as S01 |
| S03 | Split executes successfully | Upload a 5-page PDF → click "Split PDF" | Progress bar appears; thumbnails grid renders with 5 pages |
| S04 | Page count badge updates | After split | Split tab badge shows "5" (page count) |
| S05 | Split with >500 pages | Upload a 501-page PDF | Toast error "PDF has too many pages (max 500)"; no thumbnails shown |
| S06 | Replace file mid-session | Split a PDF, then drop a new file | Previous results hidden; new file info shown; old thumbnails gone |
| S07 | Clear file | Click clear/remove file icon after loading | Drop zone reappears; all state reset; split badge hidden |
| S08 | Password-protected PDF | Upload an encrypted PDF | Worker error surfaced as toast; no thumbnails shown |

---

### 2 – Merge PDF

| ID | Title | Steps | Expected Result |
|----|-------|--------|-----------------|
| M01 | Add files via file picker | Click "Add PDFs", select 3 files | Merge list shows 3 entries with filename, size, and page count |
| M02 | Add files via drag-and-drop | Drag 2 PDFs onto the merge drop zone | Files appended to merge list |
| M03 | Remove a file from the list | Click the ✕ button on one entry | Entry removed; total page count updates |
| M04 | Reorder via drag | Drag file 1 below file 2 | Order reflects drag result; output PDF order matches |
| M05 | Merge & Download | Add 2 PDFs → click "Merge & Download" | Progress shown; merged PDF downloaded; page count = sum of inputs |
| M06 | Oversized merge file | Add a file >200 MB | Toast error; file not added to list |
| M07 | Non-PDF file in merge (B1) | Add a `.jpg` renamed to `.pdf` | **Current behaviour (bug):** file added with `pageCount = '?'`; merge may fail or produce corrupt output. **Expected:** toast error; file rejected. |
| M08 | Clear all merge files | Remove all files from list | "Merge & Download" button hidden/disabled |

---

### 3 – Dark Mode Toggle

| ID | Title | Steps | Expected Result |
|----|-------|--------|-----------------|
| T01 | Default theme | Open app fresh (no localStorage) | Light mode active; ☀️ button has `active` class |
| T02 | Switch to dark | Click 🌙 button | `data-theme="dark"` set on `<html>`; all CSS variables update |
| T03 | Switch back to light | Click ☀️ button | `data-theme="light"` restored |
| T04 | Persistence across reload | Set dark mode → reload page | Dark mode still active (read from localStorage `theme` key) |

---

### 4 – File Upload Validation

| ID | Title | Steps | Expected Result |
|----|-------|--------|-----------------|
| V01 | Wrong file type – split | Attempt to upload a `.docx` file | Toast "Please select a valid PDF file."; file rejected |
| V02 | Wrong file type – merge | Attempt to add a `.png` to merge list | File silently filtered (accepts only `.pdf` / `application/pdf` MIME) |
| V03 | File too large – split | Upload a file >200 MB | Toast "File too large. Maximum size is 200MB."; file rejected |
| V04 | File too large – merge | Add a file >200 MB to merge | Toast "{name} is too large (max 200MB)."; file not added |
| V05 | Renamed non-PDF – split (B2) | Rename a `.jpg` to `.pdf` and upload | **Current behaviour (bug):** passes initial check; fails during processing. **Expected:** friendly error before processing starts. |
| V06 | Renamed non-PDF – merge (B1) | Rename a `.txt` to `.pdf` and add to merge | **Current behaviour (bug):** added with `pageCount = '?'`. **Expected:** rejected with toast. |
| V07 | Drop multiple files on split zone | Drag 3 PDFs onto split zone | Only the first file is loaded (design choice) |

---

### 5 – Download Options

| ID | Title | Steps | Expected Result |
|----|-------|--------|-----------------|
| D01 | Download ZIP (all pages) | Split PDF → click "Download All as ZIP" | ZIP downloaded containing one PDF per page, named `page_1.pdf` … `page_N.pdf` |
| D02 | Download ZIP (selected pages) | Select pages 1 and 3 → click "Download Selected as ZIP" | ZIP contains exactly `page_1.pdf` and `page_3.pdf` |
| D03 | Download single page | Click download icon on a thumbnail | Single-page PDF downloaded |
| D04 | Download range – valid | Enter From=2, To=4 → click "Download Range" | ZIP with pages 2–4 downloaded |
| D05 | Download range – invalid (reversed) | Enter From=5, To=2 | Toast "Enter a valid range…"; no download |
| D06 | Download range – out of bounds | Enter From=0 or To > total pages | Toast validation error |
| D07 | Download after delete (B4) | Delete page 2, enter range 1–3, download | **Current behaviour (bug):** range filter uses original indices; may include deleted page slot or miss pages. **Expected:** range applies to the visible, re-indexed page set. |
| D08 | Download selected – none selected | Click "Download Selected" with no selection | Button should be disabled (it is, by default) |

---

### 6 – Page Management

| ID | Title | Steps | Expected Result |
|----|-------|--------|-----------------|
| P01 | Select individual page | Click a thumbnail checkbox | Checkbox checked; "Delete Selected" and "Download Selected" buttons enabled |
| P02 | Select All | Click "Select All" | All thumbnails checked; count shown in toolbar |
| P03 | Deselect All | Click "Deselect All" | All thumbnails unchecked; bulk action buttons disabled |
| P04 | Rotate single page | Click rotate icon on a thumbnail | Thumbnail rotates 90° clockwise; rotation persisted in `state.rotations` |
| P05 | Rotate selected pages | Select 3 pages → click "Rotate Selected" | All 3 thumbnails rotate 90° |
| P06 | Delete single page | Click delete icon on a thumbnail | Thumbnail removed from grid; page count decrements |
| P07 | Delete selected pages | Select pages 2 and 4 → click "Delete Selected" | Both removed from grid |
| P08 | Restore deleted pages | Click "Restore All" / undo mechanism (if present) | All deleted pages reappear |
| P09 | Drag-reorder pages | Drag page 3 card before page 1 | Grid order updates; ZIP download respects new order |
| P10 | Reorder + download consistency | Reorder pages → download all as ZIP | ZIP entry order matches displayed order |
| P11 | Interact during ZIP creation (B7) | Trigger ZIP download → immediately delete a page | **Current behaviour (bug):** controls remain active; state can mutate mid-download. **Expected:** all page-management controls disabled while `state.busy = true`. |

---

### 7 – Responsive Design

| ID | Title | Viewport | Expected Result |
|----|-------|----------|-----------------|
| R01 | Mobile – 320 px | 320 × 568 | Header text scales down (1.3 rem); no horizontal overflow; tabs readable |
| R02 | Mobile – 375 px | 375 × 667 | Drop zone, buttons, and toolbar usable; no element clipping |
| R03 | Tablet – 600 px | 600 × 900 | `@media (max-width: 600px)` boundary; layout shifts correctly |
| R04 | Tablet – 768 px | 768 × 1024 | Thumbnails grid uses `auto-fill minmax(130px)` columns; no wrapping issues |
| R05 | Desktop – 1440 px | 1440 × 900 | Full layout; max-width container centred |
| R06 | Toast placement | Any width | Toast container fixed bottom-right; does not obscure action buttons on mobile |
| R07 | Merge list on mobile | 375 px with 5 files | File names truncate with ellipsis; ✕ buttons still tappable |

---

### 8 – Features Not Yet Implemented

The following features were requested in the test scope but **do not exist** in the current build. No UI panels, JS functions, or routes were found for them. Test cases should be created when these features are added.

| Feature | Status |
|---------|--------|
| Compress PDF | Not implemented |
| Watermark PDF | Not implemented |
| Add Page Numbers | Not implemented |
| PDF to Images | Not implemented |
| Extract Images from PDF | Not implemented |
| Password Protect PDF | Not implemented |
| Unlock (Remove Password from) PDF | Not implemented |

---

## Summary

- **42 test cases** across 7 active areas + 1 future-features section
- **7 code bugs** identified (2 high/medium security/correctness, 5 medium/low UX)
- Highest priority fixes: **B1** (corrupt merge files silently accepted), **B6** (innerHTML XSS with filenames), **B5** (worker leak on error)
