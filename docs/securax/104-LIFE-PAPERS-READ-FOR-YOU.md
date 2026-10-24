# 104 · Life papers, read for you

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested on fake data: the life workbooks and private documents are read on your machine, each open issue becomes a dated Life OS action with the vital fifth first and calendar alarms, secrets are never copied and numbers are masked. The private RAG hand-off, ticking items in the Life OS, and a weekly re-read are dated. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The ask:** keeping the life workbooks current by hand is friction, and it is hard to know whether every open issue is
closed. Read them for me, find the patterns, put the few things that matter first (80/20), and do the same for documents I
upload (insurance policies, bank statements, ID scans): catch a policy about to lapse or a missing nominee, set the calendar
alarms, and keep it all private.

## 1. Start here: your papers are the input

Filling a spreadsheet first is the friction, so you do not have to. The Life OS Inbox opens with **Your papers**: the few
papers that hold the numbers, why each matters and where to get it. Run `./securax lifeos papers` for the same list in the
terminal.

| Paper | What is read from it |
|---|---|
| Form 16 (latest year) | annual income, taxable income, tax paid |
| AIS or Form 26AS | tax deducted on all income |
| CDSL or NSDL consolidated account statement (CAS) | the value of your shares and funds |
| Bank statements, 12 months, each account | money in, money out, closing balance; the saving rate against income |
| EPF passbook, NPS statement | balances and nominees |
| Insurance policies, Aadhaar and PAN, loan statements | renewal dates, nominees, missing IDs, what is owed |

Save each one, in any format (PDF, scan, photo, Excel, Word, CSV or text) and with any name, in `vault/life/docs/`, then run
`./securax lifeos docs`. Each paper is recognised by what it says. A paper still missing is an action in the Inbox (the first
three are in the vital few), and it ticks itself off once the paper is in. Only totals are kept, never an account, PAN or
other identifier.

## 2. What it does

| You have | Run | What arrives |
|---|---|---|
| Your life workbooks (.xlsx) | `./securax lifeos import workbook` | every open issue as a dated Life OS action; the vital fifth first |
| Policies, statements, ID scans (PDF, JPG, PNG) in `vault/life/docs/` | `./securax lifeos docs` | renewals, lapses and missing nominees as dated issues |
| Either | (automatic) | calendar alarms 7 days and 1 day before each vital deadline, in `vault/life/` |

The Life OS Inbox shows **The vital few** first and folds the rest. When the workbook or the document shows an issue fixed, the
next import ticks it off by itself, so the Inbox is the one place to see what is still open.

**No file named?** The workbook import looks in `vault/life/`, Downloads, Documents and Desktop (the Windows ones on WSL too),
and takes the newest Guiding Map and growth-tracker workbooks.

## 3. What it looks for

Sheets are recognised by their column headers, so a renamed sheet still works.

| In a sheet like | It raises |
|---|---|
| a register of documents and accounts | a missing nominee; a login outside the password manager; a PIN or password written in the sheet; an expiry within 90 days or passed |
| a nomination tracker | no nominee, or one marked for update |
| an emergency binder checklist | each item not yet in it |
| a credentials list | logins outside the password manager, and no place recorded for 2FA backup codes (grouped, one action each) |
| personal details | a household member (self, spouse, children, parents) without an Aadhaar or PAN on record; "NA" counts as missing |
| goals, certifications, a roadmap | each goal or task not done; one past its date is marked late, with "decide: a new date, a smaller step, or drop it" |
| banking details, a skills or tech-stack gap list | each action item |
| insurance needs, certification renewals | each cover with a gap; a certification expiring within 120 days |

**80/20:** every item is scored by how much its area matters (identity, insurance, nominees, security and health highest) and
by how soon it is due. The top fifth is the vital few.

For documents, the text is read on the machine: `pdftotext` for PDFs, and the Tesseract OCR engine for scans and photos
(`sudo apt install poppler-utils tesseract-ocr`, once). Each document is classed (insurance, bank statement, identity, loan,
investment, property, vehicle), and its expiry, renewal, premium-due or maturity date and its nominee are found.

## 4. Privacy, by design

- **Nothing leaves the machine.** No network call and no cloud model: the reading is plain pattern matching and local OCR.
- **Secrets are never copied.** A PIN or password found in a sheet becomes an action to remove it, without the value.
- **Numbers are never kept in full.** Account, policy and ID numbers are not read into the workbook output at all; the
  document register keeps only the last four characters (`XXXX1234`).
- **Everything written is private:** `vault/life/` is readable by you only, and it and `portal/inbox-import.json` are
  git-ignored. The repository holds the code and fake test data only.

## 5. Next, with dates

| Step | By |
|---|---|
| Hand a document's text to the private Docs workspace (the estate's own RAG), so "when does my health cover renew?" is answered from your papers | 2026-11-08 |
| A Life OS screen to tick a register item (nominee set, Aadhaar recorded) without opening the workbook; the next import reads it back | 2026-11-15 |
| Upload a paper straight from the Life OS on the phone (a drop zone that saves it to `vault/life/docs/` on the laptop, signed in) | 2026-11-15 |
| A weekly routine that re-reads the workbooks and documents by itself, so the Inbox is never older than a week | 2026-11-01 |

## 6. Scan a paper with your phone's camera

Open the Life OS Inbox on your phone and tap **📷 Scan a document**. Your camera opens; photograph the policy, bill or
letter. The text is read **on the phone itself** — the OCR engine (tesseract.js, about 6 MB) loads the first time you
scan and is then cached for offline use — and dropped into the capture box, where you check the words and tap **Add**.
It becomes an action with a date or a note, exactly like anything else you capture.

Nothing is uploaded: the photo and its text never leave your device. If the engine cannot load (an old phone, no space),
the box simply stays empty and you type the note by hand — scanning never blocks capture.

## 7. The lens: it understands what it sees (and spots scams)

Scanning drops the words into the Inbox. The **lens** goes one step further: it *understands* them, on your own
device, with no upload and no cloud model.

- **It classes what you captured** — a bill, a policy, an ID, an appointment — and picks the right kind for you.
- **It pulls out the amount and the due date**, so a scanned bill arrives in the Inbox already dated. No typing.
- **It spots scams before you tap.** An OTP request, a "your KYC is blocked" message, a prize, a link to click, a
  UPI *collect*-request sent to you — each is flagged with a red banner and the reasons in plain words. This is the
  one thing a BFSI-grade Life OS should do that a note-taking app never will.
- **It learns, on the phone.** When you tap **"Yes, it is a scam"** or **"This one is safe"**, the lens nudges its
  own weights, kept on the device in `gm_lens_model` (bounded). It gets sharper the more you use it, and nothing you
  teach it ever leaves the phone.

Today the understanding is explainable heuristics plus that on-device learner — deliberately, because a security
product must be able to say *why* it flagged something, and must run offline. A heavier on-device model is the next
step, and it drops in behind the same `gmLensRead` interface.

### The rails: one sense today, many tomorrow

This is built as a **lens engine**, not a one-off feature. A lens is `{ id, name, test(text), read(text) }`, registered
with `gmLensRegister(...)`. The capture box, the warning banner and the learning do not know or care which lens
produced a reading. So the future senses — ambient voice capture ("I'll send that Friday" → an action), a
compare-two-offers lens, a family-papers lens — are **plug-and-play**: each is one small lens that registers the same
shape, and the engine, the UI and the privacy promise stay exactly as they are.

This is the SixthSense idea — closing the gap between the physical world and your Life OS — made private and
security-grade: point your phone at the world, and it becomes a decision you can trust.
