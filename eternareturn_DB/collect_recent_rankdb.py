from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from Get_User_data_py import SendERData


MAX_CONSECUTIVE_MISSING = 50
DEFAULT_MAX_SCAN_COUNT = 5000
RECENT_HOURS_CUTOFF = 2
REQUEST_DELAY_SECONDS = 1.0


@dataclass
class CollectionSummary:
    scanned: int = 0
    inserted_rank: int = 0
    inserted_normal: int = 0
    skipped_empty: int = 0
    skipped_mode: int = 0
    stopped_recent: bool = False
    stopped_missing_cap: bool = False


def collect_recent_rankdb(
    *,
    max_scan_count: int = DEFAULT_MAX_SCAN_COUNT,
    max_consecutive_missing: int = MAX_CONSECUTIVE_MISSING,
    recent_hours_cutoff: int = RECENT_HOURS_CUTOFF,
    request_delay_seconds: float = REQUEST_DELAY_SECONDS,
) -> CollectionSummary:
    sender = SendERData(game_id="0")
    sender.first_db_check()

    max_game_id = sender.get_max_gameid()
    if max_game_id is None:
        raise RuntimeError("Could not read MAX(gameid) from rankdb_v2.")

    summary = CollectionSummary()
    consecutive_missing = 0
    start_game_id = int(max_game_id) + 1
    end_game_id = start_game_id + max_scan_count

    print(f"[collector] start_game_id={start_game_id}")
    print(f"[collector] end_game_id={end_game_id - 1}")
    print(f"[collector] recent_hours_cutoff={recent_hours_cutoff}")
    print(f"[collector] max_consecutive_missing={max_consecutive_missing}")
    print(f"[collector] request_delay_seconds={request_delay_seconds}")

    for game_id in range(start_game_id, end_game_id):
        summary.scanned += 1
        sender.put_game_id(str(game_id))

        ok = sender.fetch_and_build()
        if not ok:
            consecutive_missing += 1
            summary.skipped_empty += 1
            sender.clear_temp_data()
            print(f"[collector] skip missing/empty game_id={game_id} consecutive_missing={consecutive_missing}")

            if consecutive_missing >= max_consecutive_missing:
                summary.stopped_missing_cap = True
                print("[collector] stopping because consecutive missing game ids reached the cap.")
                break
            if request_delay_seconds > 0:
                time.sleep(request_delay_seconds)
            continue

        consecutive_missing = 0
        frame = sender.player_df
        if frame is None or frame.empty:
            summary.skipped_empty += 1
            sender.clear_temp_data()
            print(f"[collector] skip empty dataframe game_id={game_id}")
            if request_delay_seconds > 0:
                time.sleep(request_delay_seconds)
            continue

        first_startdtm: Optional[str] = frame["startDtm"].iloc[0] if "startDtm" in frame.columns else None
        if not sender.is_older_than_hours(first_startdtm, hours=recent_hours_cutoff):
            summary.stopped_recent = True
            sender.clear_temp_data()
            print(
                "[collector] stopping because the newest fetched match is still inside the recent cutoff: "
                f"game_id={game_id}, startDtm={first_startdtm}"
            )
            break

        matching_mode = int(frame["matchingmode"].iloc[0])
        if matching_mode == 3:
            sender.send_db(machingMode=3)
            summary.inserted_rank += 1
            print(f"[collector] inserted rankdb_v2 game_id={game_id}")
        elif matching_mode == 2:
            summary.skipped_mode += 1
            sender.clear_temp_data()
            print(f"[collector] skip normal mode game_id={game_id}")
        else:
            summary.skipped_mode += 1
            sender.clear_temp_data()
            print(f"[collector] skip unsupported matchingMode={matching_mode} game_id={game_id}")

        if request_delay_seconds > 0:
            time.sleep(request_delay_seconds)

    print(
        "[collector] finished "
        f"scanned={summary.scanned} rank={summary.inserted_rank} normal={summary.inserted_normal} "
        f"empty={summary.skipped_empty} mode_skip={summary.skipped_mode} "
        f"stopped_recent={summary.stopped_recent} stopped_missing_cap={summary.stopped_missing_cap}"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-scan-count", type=int, default=int(os.getenv("MAX_SCAN_COUNT", DEFAULT_MAX_SCAN_COUNT)))
    parser.add_argument(
        "--max-consecutive-missing",
        type=int,
        default=int(os.getenv("MAX_CONSECUTIVE_MISSING", MAX_CONSECUTIVE_MISSING)),
    )
    parser.add_argument(
        "--recent-hours-cutoff",
        type=int,
        default=int(os.getenv("RECENT_HOURS_CUTOFF", RECENT_HOURS_CUTOFF)),
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=float(os.getenv("REQUEST_DELAY_SECONDS", REQUEST_DELAY_SECONDS)),
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    print(f"[collector] working_directory={project_root}")
    collect_recent_rankdb(
        max_scan_count=args.max_scan_count,
        max_consecutive_missing=args.max_consecutive_missing,
        recent_hours_cutoff=args.recent_hours_cutoff,
        request_delay_seconds=args.request_delay_seconds,
    )
