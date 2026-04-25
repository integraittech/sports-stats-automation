# Sports Stats Automation

Personal sports research and results-tracking automation, starting with an
NHL-only MVP.

This project is not a betting recommendation tool. The goal is to automate
repetitive sports stat gathering, write research data into Google Sheets, and
later update user-entered picks/results after games finish.

## First Milestone

Create a daily NHL slate research workflow:

1. Pull today's NHL schedule.
2. For each matchup, gather placeholder-ready inputs for:
   - Last 10 head-to-head games.
   - Each team's last 5 games.
3. Calculate placeholder-ready metrics for:
   - First-period over 1.5 goals counts and percentages.
   - Full-game over 5.5 goals counts and percentages.
   - Goals for, goals against, total goals.
   - Zero-goal and 2+ goal first periods.
4. Write one row per matchup into a Google Sheet.

The NHL data client and calculation logic are still placeholders. The Google
Sheets smoke-test command can make a real append call once credentials are set.

## Project Structure

```text
config/
  settings.yaml
src/
  main_daily_slate.py
  main_update_results.py
  nhl/
    api_client.py
    slate.py
    history.py
    calculations.py
    results.py
  sheets/
    client.py
    schemas.py
    writer.py
    reader.py
  utils/
    dates.py
    logging.py
tests/
  test_nhl_calculations.py
```

## Setup

Use Python 3.10 or newer. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Then fill in the Google Sheets values in `.env`.

## Google Sheets API Setup

Create a Google Cloud project and enable the Google Sheets API.

Create a service account, download its JSON key, and share your target Google
Sheet with the service account email address.

Set these values in `.env`:

```bash
GOOGLE_SHEETS_SPREADSHEET_ID=your_google_sheet_id_here
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
GOOGLE_SHEETS_APPEND_RANGE=Daily_Slate!A:B
```

The spreadsheet ID is the long ID in the Google Sheet URL. The append range can
stay as `Daily_Slate!A:B` if your sheet has a `Daily_Slate` tab.

## Commands

Append a Google Sheets smoke-test row:

```bash
python -m src.main_daily_slate
```

This writes:

```text
TEST | It works
```

Future postgame result workflow:

```bash
python -m src.main_update_results
```

`src.main_update_results` is still a placeholder.
