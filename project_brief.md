I want to scope an MVP for a personal sports research and results-tracking workflow.

Important:
This is NOT a betting recommendation tool. It should not suggest wagers or optimize gambling decisions. The purpose is to automate repetitive sports stat gathering, update historical tracking sheets, and display analytics from user-entered picks/results.

User workflow summary:
The user currently researches NHL daily slates manually. For each NHL matchup, he checks StatMuse and other sources to gather:
- Last 10 head-to-head games between the teams
- How often those H2H games went over 1.5 goals in the first period
- How often those H2H games went over 5.5 total goals
- First period goals in those matchups
- Each team’s last 5 games
- How often each team had first period over 1.5 goals in last 5
- How often each team had full game over 5.5 goals in last 5
- Goals scored and allowed in last 5 to 10 games
- Total goals
- Games with zero first period goals
- Games with 2+ first period goals

This takes about 7 minutes per matchup. On a 15-game NHL slate, this can take 1.5 to 2 hours.

After games finish, he manually updates:
- Final score / final total
- First period total
- Whether his pick was right or wrong
- Whether the GPT pick was right or wrong
- Row color red/green if a pick hit or missed

This takes another 20 to 40 minutes.

Current tools:
- StatMuse for NHL and NBA
- NHL.com
- NBA.com
- NFL.com
- ESPN
- Tapology
- PropStock AI/Cash for UFC

Sports:
- NHL is the main current focus
- UFC is also tracked
- NBA lightly
- NFL planned later

NHL markets:
- First period over/under 1.5 goals
- Full game over/under 5.5 goals

UFC markets:
- Fighter winner
- Method of victory: TKO, submission, decision

NBA/NFL future:
- Mostly scoring totals and player props

Current tracking:
- Mostly spreadsheet-based
- Parlays are not tracked as structured parent/child records
- He uses color coding in the matchup column:
  - light blue if included in a parlay
  - green if it hit
  - red if it missed
- Sportsbook name is checked but not recorded
- Stake, odds, payout, profit/loss are loosely tracked in a separate sheet
- Profit/loss is mostly manually entered
- Desktop dashboard is fine
- Manual review is acceptable if the system is unsure
- Saving 50% to 70% of the time would already be valuable
- Accuracy needs to be high enough that he does not have to re-check everything

MVP goal:
Build an NHL-only daily slate research automation using Google Sheets as the database/interface.

Recommended stack:
- Google Sheets as input/output/database
- Python for the stat calculation engine
- n8n or cron for scheduling/orchestration
- Sports data API for NHL game schedule, final scores, and period-by-period scoring
- Looker Studio or simple web dashboard for analytics

Phase 1 MVP:
1. Pull today’s NHL slate.
2. For each matchup, pull historical games:
   - last 10 head-to-head
   - each team’s last 5 games
   - optionally each team’s last 10 games
3. Calculate:
   - H2H first period over 1.5 count/percentage
   - H2H full game over 5.5 count/percentage
   - team last 5 first period over 1.5 count/percentage
   - team last 5 full game over 5.5 count/percentage
   - team goals for
   - team goals against
   - total goals
   - zero-goal first periods
   - 2+ goal first periods
4. Write all results into a Google Sheet.
5. Let the user manually enter:
   - My Pick
   - GPT Pick
   - Parlay flag
6. After games finish, pull final scores and first-period scores.
7. Update:
   - final first period total
   - final game total
   - My Pick result
   - GPT Pick result
8. Send unresolved/uncertain items to a manual review area.

Possible sheet tabs:
1. Daily_Slate
2. Raw_Games
3. Picks
4. Profit_Loss
5. Dashboard_Data
6. Manual_Review

Key technical concern:
The API must provide NHL historical games with period-by-period scoring. The most important requirement is first period goals and full game totals.

Please help me:
1. Validate the architecture.
2. Identify the best NHL data sources/API options for period-by-period historical scoring.
3. Recommend a data model for Google Sheets.
4. Define the first prototype.
5. Estimate complexity.
6. Provide a phased build plan.
7. Suggest sample Python modules/functions.
8. List the edge cases we need to handle.