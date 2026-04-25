"""Update Bets results."""

from __future__ import annotations

from src.nhl.results import (
    FinalGameResult,
    get_final_game_result,
    grade_pick,
    parse_game_teams,
)
from src.sheets.reader import BetsRow, read_bets_rows
from src.sheets.writer import (
    ensure_bets_headers,
    update_bets_gpt_profit_loss,
    update_bets_gpt_result,
    update_bets_parlay_result,
    update_bets_profit_loss,
    update_bets_result,
)


def main() -> None:
    """Grade supported Bets rows and write empty Result cells."""
    ensure_bets_headers()
    rows = read_bets_rows()
    game_cache: dict[tuple[str, str, str], FinalGameResult | None] = {}
    updated_count = 0
    skipped_count = 0
    profit_loss_updated_count = 0
    profit_loss_skipped_count = 0
    gpt_result_updated_count = 0
    gpt_result_skipped_count = 0
    gpt_profit_loss_updated_count = 0
    gpt_profit_loss_skipped_count = 0
    row_results: dict[int, str] = {}

    for row in rows:
        result = row.result
        if _should_grade(row):
            result = _grade_row(row, game_cache)
            if result is None:
                skipped_count += 1
            else:
                update_bets_result(row.row_number, result)
                updated_count += 1
        else:
            skipped_count += 1

        profit_loss = calculate_profit_loss(row.stake, row.odds, result)
        if row.profit_loss or profit_loss is None:
            profit_loss_skipped_count += 1
        else:
            update_bets_profit_loss(row.row_number, profit_loss)
            profit_loss_updated_count += 1

        gpt_result = row.gpt_result
        if _should_grade_gpt(row):
            gpt_result = _grade_pick_for_row(row, row.gpt_pick, game_cache)
            if gpt_result is None:
                gpt_result_skipped_count += 1
            else:
                update_bets_gpt_result(row.row_number, gpt_result)
                gpt_result_updated_count += 1
        else:
            gpt_result_skipped_count += 1

        gpt_profit_loss = calculate_profit_loss(row.stake, row.odds, gpt_result)
        if row.gpt_profit_loss or gpt_profit_loss is None:
            gpt_profit_loss_skipped_count += 1
        else:
            update_bets_gpt_profit_loss(row.row_number, gpt_profit_loss)
            gpt_profit_loss_updated_count += 1

        row_results[row.row_number] = result

    parlays_processed_count = update_parlays(rows, row_results)

    print(f"Updated {updated_count} Bets result rows.")
    print(f"Skipped {skipped_count} Bets rows.")
    print(f"Updated {profit_loss_updated_count} Bets profit/loss rows.")
    print(f"Skipped {profit_loss_skipped_count} Bets profit/loss rows.")
    print(f"Updated {gpt_result_updated_count} GPT result rows.")
    print(f"Skipped {gpt_result_skipped_count} GPT result rows.")
    print(f"Updated {gpt_profit_loss_updated_count} GPT profit/loss rows.")
    print(f"Skipped {gpt_profit_loss_skipped_count} GPT profit/loss rows.")
    print(f"Processed {parlays_processed_count} parlays.")


def _should_grade(row: BetsRow) -> bool:
    return bool(row.pick) and not row.result


def _should_grade_gpt(row: BetsRow) -> bool:
    return bool(row.gpt_pick) and not row.gpt_result


def _supported_bet_type(bet_type: str) -> bool:
    return bet_type.strip().lower() in {"full game", "1p"}


def _grade_row(
    row: BetsRow,
    game_cache: dict[tuple[str, str, str], FinalGameResult | None],
) -> str | None:
    return _grade_pick_for_row(row, row.pick, game_cache)


def _grade_pick_for_row(
    row: BetsRow,
    pick: str,
    game_cache: dict[tuple[str, str, str], FinalGameResult | None],
) -> str | None:
    teams = parse_game_teams(row.game)
    if teams is None or row.line is None or not _supported_bet_type(row.bet_type):
        return None

    away_team, home_team = teams
    cache_key = (row.date, away_team, home_team)
    if cache_key not in game_cache:
        game_cache[cache_key] = get_final_game_result(
            date_string=row.date,
            away_team=away_team,
            home_team=home_team,
        )

    final_result = game_cache[cache_key]
    if final_result is None:
        return None

    return grade_pick(pick, row.bet_type, row.line, final_result)


def calculate_profit_loss(
    stake: float | None,
    odds: float | None,
    result: str,
) -> float | None:
    """Calculate row-level profit/loss from stake, odds, and result."""
    if stake is None or odds is None or not result:
        return None

    result_text = result.strip().lower()
    if result_text == "win":
        if odds > 0:
            return stake * (odds / 100)
        if odds < 0:
            return stake * (100 / abs(odds))
        return None
    if result_text == "loss":
        return -stake
    if result_text == "push":
        return 0
    return None


def update_parlays(rows: list[BetsRow], row_results: dict[int, str]) -> int:
    """Calculate and write parlay result values for complete parlays."""
    processed_count = 0

    for parlay_rows in _parlay_groups(rows).values():
        parlay_result = calculate_parlay_result(parlay_rows, row_results)
        if parlay_result is None:
            continue

        result, profit_loss = parlay_result
        wrote_row = False
        for row in parlay_rows:
            if row.parlay_result or row.parlay_profit_loss:
                continue
            update_bets_parlay_result(row.row_number, result, profit_loss)
            wrote_row = True
        if wrote_row:
            processed_count += 1

    return processed_count


def calculate_parlay_result(
    rows: list[BetsRow],
    row_results: dict[int, str],
) -> tuple[str, float] | None:
    """Calculate one parlay's overall result and profit/loss."""
    if not rows:
        return None

    stake = rows[0].stake
    if stake is None:
        return None

    total_odds = 1.0
    results = []
    for row in rows:
        result = row_results.get(row.row_number, row.result).strip()
        if not result or row.odds is None:
            return None
        decimal_odds = american_odds_to_decimal(row.odds)
        if decimal_odds is None:
            return None
        results.append(result.lower())
        total_odds *= decimal_odds

    if any(result == "loss" for result in results):
        return "Loss", -stake
    if all(result == "win" for result in results):
        return "Win", (stake * total_odds) - stake
    return None


def american_odds_to_decimal(odds: float) -> float | None:
    """Convert American odds to decimal odds."""
    if odds > 0:
        return 1 + (odds / 100)
    if odds < 0:
        return 1 + (100 / abs(odds))
    return None


def _parlay_groups(rows: list[BetsRow]) -> dict[str, list[BetsRow]]:
    groups: dict[str, list[BetsRow]] = {}
    for row in rows:
        if row.in_parlay.strip().lower() != "yes" or not row.parlay_id:
            continue
        groups.setdefault(row.parlay_id, []).append(row)
    return groups


if __name__ == "__main__":
    main()
