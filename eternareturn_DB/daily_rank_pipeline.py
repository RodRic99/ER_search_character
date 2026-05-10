from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from ER_db_training import ERDBClassification
from Get_User_data_py import SendERData
from generate_all_character_combo_predictions import BatchComboPredictor
from artifact_publisher import S3ArtifactPublisher


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"
PREDICTION_DIR = BASE_DIR / "predictions"


@dataclass
class DailyCollectionSummary:
    scanned: int = 0
    inserted_rank: int = 0
    skipped_empty: int = 0
    skipped_mode: int = 0
    stopped_cutoff: bool = False
    stopped_missing_cap: bool = False
    start_game_id: Optional[int] = None
    stop_game_id: Optional[int] = None
    cutoff_datetime: Optional[str] = None


def collect_rank_until_cutoff(
    *,
    cutoff_datetime: datetime,
    max_scan_count: int = 200000,
    max_consecutive_missing: int = 500,
) -> DailyCollectionSummary:
    sender = SendERData(game_id="0")
    sender.first_db_check()

    max_game_id = sender.get_max_gameid()
    if max_game_id is None:
        raise RuntimeError("Could not read MAX(gameid) from rankdb_v2.")

    summary = DailyCollectionSummary(
        start_game_id=int(max_game_id) + 1,
        cutoff_datetime=cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
    )
    consecutive_missing = 0
    end_game_id = summary.start_game_id + max_scan_count

    print(f"[daily-pipeline] collect start_game_id={summary.start_game_id}")
    print(f"[daily-pipeline] collect end_game_id={end_game_id - 1}")
    print(f"[daily-pipeline] cutoff_datetime={summary.cutoff_datetime}")

    for game_id in range(summary.start_game_id, end_game_id):
        summary.scanned += 1
        sender.put_game_id(str(game_id))

        ok = sender.fetch_and_build()
        if not ok:
            consecutive_missing += 1
            summary.skipped_empty += 1
            sender.clear_temp_data()
            print(f"[daily-pipeline] skip missing/empty game_id={game_id} consecutive_missing={consecutive_missing}")

            if consecutive_missing >= max_consecutive_missing:
                summary.stopped_missing_cap = True
                summary.stop_game_id = game_id
                print("[daily-pipeline] stopping because consecutive missing game ids reached the cap.")
                break
            continue

        consecutive_missing = 0
        frame = sender.player_df
        if frame is None or frame.empty:
            summary.skipped_empty += 1
            sender.clear_temp_data()
            print(f"[daily-pipeline] skip empty dataframe game_id={game_id}")
            continue

        first_startdtm = frame["startDtm"].iloc[0] if "startDtm" in frame.columns else None
        if not sender.is_before_datetime(first_startdtm, cutoff_datetime):
            summary.stopped_cutoff = True
            summary.stop_game_id = game_id
            sender.clear_temp_data()
            print(
                "[daily-pipeline] stopping because fetched match crossed the daily cutoff: "
                f"game_id={game_id}, startDtm={first_startdtm}, cutoff={summary.cutoff_datetime}"
            )
            break

        matching_mode = int(frame["matchingmode"].iloc[0])
        if matching_mode == 3:
            sender.send_db(machingMode=3)
            summary.inserted_rank += 1
            print(f"[daily-pipeline] inserted rankdb_v2 game_id={game_id}")
        else:
            summary.skipped_mode += 1
            sender.clear_temp_data()
            print(f"[daily-pipeline] skip matchingMode={matching_mode} game_id={game_id}")

    print(
        "[daily-pipeline] collection finished "
        f"scanned={summary.scanned} rank={summary.inserted_rank} "
        f"empty={summary.skipped_empty} mode_skip={summary.skipped_mode} "
        f"stopped_cutoff={summary.stopped_cutoff} stopped_missing_cap={summary.stopped_missing_cap}"
    )
    return summary


def run_training_and_prediction(*, cutoff_datetime: datetime):
    er_db = ERDBClassification()
    er_db.conect_db(rebuild_train_base=True)
    position_synergy_cache_df = er_db.build_position_synergy_cache_df(
        cutoff_date=cutoff_datetime.date().isoformat()
    )
    position_synergy_table = er_db.save_position_synergy_cache(position_synergy_cache_df)
    print(
        f"[daily-pipeline] position synergy cache saved: table={position_synergy_table}, "
        f"rows={len(position_synergy_cache_df)}"
    )
    er_db.split_df_by_tier_group()

    training_device = os.getenv("TRAINING_XGB_DEVICE", "cpu").strip().lower()
    model_params = {
        "n_estimators": 6500,
        "learning_rate": 0.03,
        "max_depth": 4,
        "min_child_weight": 12,
        "reg_alpha": 1.0,
        "reg_lambda": 3.0,
        "subsample": 0.7,
        "colsample_bytree": 0.7,
        "early_stopping_rounds": 50,
    }
    if training_device and training_device != "auto":
        model_params["device"] = training_device
    print(f"[daily-pipeline] xgboost device={model_params.get('device', 'default')}")

    results_df = er_db.train_xgb_by_tier_group(
        target_col="avg_getmmr",
        cutoff_datetime=cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        recent_days=7,
        medium_days=14,
        recent_weight=1.0,
        medium_weight=0.8,
        old_weight=0.3,
        rankpoint_threshold=6100,
        model_params=model_params,
    )
    print(results_df)
    if results_df.empty:
        raise RuntimeError("Training returned no models/results.")

    er_db.save_models(save_dir=str(MODEL_DIR))

    model_path = MODEL_DIR / "xgb_model_all_tiers.json"
    feature_path = MODEL_DIR / "xgb_model_all_tiers_features.csv"
    encoder_path = MODEL_DIR / "xgb_model_all_tiers_label_encoders.json"
    predictor = BatchComboPredictor(
        model_path=model_path,
        feature_path=feature_path,
        encoder_path=encoder_path,
    )
    try:
        prediction_df, table_name, dropped_tables = predictor.predict_all_character_combinations()
    finally:
        predictor.close()

    absolute_score_cache_df = er_db.build_absolute_score_cache_df(
        prediction_df=prediction_df,
        position_synergy_cache_df=position_synergy_cache_df,
        cutoff_date=cutoff_datetime.date().isoformat(),
    )
    absolute_score_table = er_db.save_absolute_score_cache(absolute_score_cache_df)
    print(
        f"[daily-pipeline] absolute score cache saved: table={absolute_score_table}, "
        f"rows={len(absolute_score_cache_df)}"
    )

    return (
        results_df,
        prediction_df,
        table_name,
        dropped_tables,
        position_synergy_table,
        position_synergy_cache_df,
        absolute_score_table,
        absolute_score_cache_df,
    )


def build_cutoff_datetime(run_date: Optional[str]) -> datetime:
    if run_date:
        target_date = datetime.strptime(run_date, "%Y-%m-%d").date()
    else:
        target_date = datetime.now().date()
    return datetime.combine(target_date, time.min)


def save_summary(summary_payload):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    cutoff_label = summary_payload["cutoff_datetime"].replace(":", "").replace(" ", "_")
    output_path = REPORT_DIR / f"daily_rank_pipeline_summary_{cutoff_label}.json"
    output_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[daily-pipeline] summary saved to {output_path}")
    return output_path


def export_pipeline_reports(
    *,
    cutoff_datetime: datetime,
    training_results_df,
    prediction_df,
    position_synergy_cache_df,
    absolute_score_cache_df,
):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = cutoff_datetime.strftime("%Y%m%d_%H%M%S")

    training_path = REPORT_DIR / f"daily_training_results_{timestamp}.csv"
    prediction_path = PREDICTION_DIR / f"daily_all_character_predictions_{timestamp}.csv"
    position_path = REPORT_DIR / f"daily_position_synergy_cache_{timestamp}.csv"
    score_path = REPORT_DIR / f"daily_absolute_score_cache_{timestamp}.csv"

    training_results_df.to_csv(training_path, index=True, encoding="utf-8-sig")
    prediction_df.to_csv(prediction_path, index=False, encoding="utf-8-sig")
    position_synergy_cache_df.to_csv(position_path, index=False, encoding="utf-8-sig")
    absolute_score_cache_df.to_csv(score_path, index=False, encoding="utf-8-sig")

    print(f"[daily-pipeline] exported training results to {training_path}")
    print(f"[daily-pipeline] exported predictions to {prediction_path}")
    print(f"[daily-pipeline] exported position cache to {position_path}")
    print(f"[daily-pipeline] exported score cache to {score_path}")

    return {
        "training_results": training_path,
        "predictions": prediction_path,
        "position_synergy": position_path,
        "absolute_score": score_path,
    }


def publish_training_artifacts(
    *,
    cutoff_datetime: datetime,
    summary_path: Path,
    exported_report_paths: dict[str, Path],
    prediction_table: str,
    position_synergy_table: str,
    absolute_score_table: str,
    collection_summary: DailyCollectionSummary,
    training_results_df,
):
    publisher = S3ArtifactPublisher.from_env()
    if publisher is None:
        print("[daily-pipeline] TRAINING_ARTIFACT_BUCKET not set. Skipping S3 artifact publishing.")
        return None

    timestamp = cutoff_datetime.strftime("%Y%m%d_%H%M%S")
    model_suffix = os.getenv("TRAINING_MODEL_SUFFIX", "").strip()

    model_artifacts = [
        (MODEL_DIR / "xgb_model_all_tiers.json", f"models/{timestamp}/xgb_model_all_tiers.json"),
        (MODEL_DIR / "xgb_model_all_tiers_features.csv", f"models/{timestamp}/xgb_model_all_tiers_features.csv"),
        (MODEL_DIR / "xgb_model_all_tiers_label_encoders.json", f"models/{timestamp}/xgb_model_all_tiers_label_encoders.json"),
    ]
    if model_suffix:
        model_artifacts.extend(
            [
                (MODEL_DIR / f"xgb_model_all_tiers_{model_suffix}.json", f"models/{timestamp}/xgb_model_all_tiers_{model_suffix}.json"),
                (MODEL_DIR / f"xgb_model_all_tiers_{model_suffix}_features.csv", f"models/{timestamp}/xgb_model_all_tiers_{model_suffix}_features.csv"),
                (MODEL_DIR / f"xgb_model_all_tiers_{model_suffix}_label_encoders.json", f"models/{timestamp}/xgb_model_all_tiers_{model_suffix}_label_encoders.json"),
            ]
        )

    published_files = []
    published_files.extend(
        publisher.upload_files(
            [
                (path, s3_key)
                for path, s3_key in model_artifacts
                if Path(path).exists()
            ]
        )
    )
    published_files.extend(
        publisher.upload_files(
            [
                (summary_path, f"reports/{timestamp}/{summary_path.name}"),
                (
                    exported_report_paths["training_results"],
                    f"reports/{timestamp}/{exported_report_paths['training_results'].name}",
                ),
                (
                    exported_report_paths["predictions"],
                    f"predictions/{timestamp}/{exported_report_paths['predictions'].name}",
                ),
                (
                    exported_report_paths["position_synergy"],
                    f"reports/{timestamp}/{exported_report_paths['position_synergy'].name}",
                ),
                (
                    exported_report_paths["absolute_score"],
                    f"reports/{timestamp}/{exported_report_paths['absolute_score'].name}",
                ),
            ]
        )
    )

    manifest = publisher.publish_manifest(
        pipeline_name="daily-rank-pipeline",
        cutoff_datetime=cutoff_datetime,
        artifact_group="training-run",
        files=published_files,
        metadata={
            "prediction_table": prediction_table,
            "position_synergy_table": position_synergy_table,
            "absolute_score_table": absolute_score_table,
            "collection_summary": asdict(collection_summary),
            "training_results": training_results_df.reset_index().rename(columns={"index": "tier"}).to_dict(orient="records"),
        },
    )

    latest_manifest = publisher.upload_json(
        {
            "latest_cutoff_datetime": cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "manifest_key": manifest.s3_key,
            "prediction_table": prediction_table,
            "position_synergy_table": position_synergy_table,
            "absolute_score_table": absolute_score_table,
        },
        "latest/latest_training_manifest.json",
    )
    print(f"[daily-pipeline] uploaded {len(published_files)} files to s3://{publisher.bucket}/{publisher.prefix}")
    print(f"[daily-pipeline] latest manifest updated at s3://{publisher.bucket}/{latest_manifest.s3_key}")
    return {
        "bucket": publisher.bucket,
        "prefix": publisher.prefix,
        "manifest_key": manifest.s3_key,
        "latest_manifest_key": latest_manifest.s3_key,
        "file_count": len(published_files),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-date", help="Cutoff date in YYYY-MM-DD. Pipeline collects matches strictly before this date 00:00:00.")
    parser.add_argument("--max-scan-count", type=int, default=200000)
    parser.add_argument("--max-consecutive-missing", type=int, default=500)
    args = parser.parse_args()

    cutoff_datetime = build_cutoff_datetime(args.run_date)
    collection_summary = collect_rank_until_cutoff(
        cutoff_datetime=cutoff_datetime,
        max_scan_count=args.max_scan_count,
        max_consecutive_missing=args.max_consecutive_missing,
    )
    (
        training_results_df,
        prediction_df,
        table_name,
        dropped_tables,
        position_synergy_table,
        position_synergy_cache_df,
        absolute_score_table,
        absolute_score_cache_df,
    ) = run_training_and_prediction(
        cutoff_datetime=cutoff_datetime
    )

    summary_payload = {
        "cutoff_datetime": cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "collection_summary": asdict(collection_summary),
        "training_results": training_results_df.reset_index().rename(columns={"index": "tier"}).to_dict(orient="records"),
        "prediction_table": table_name,
        "prediction_rows": int(len(prediction_df)),
        "position_synergy_table": position_synergy_table,
        "position_synergy_rows": int(len(position_synergy_cache_df)),
        "absolute_score_table": absolute_score_table,
        "absolute_score_rows": int(len(absolute_score_cache_df)),
        "absolute_score_metrics": absolute_score_cache_df.to_dict(orient="records"),
        "top_position_synergies": position_synergy_cache_df.head(10).to_dict(orient="records"),
        "top_predictions": prediction_df[
            ["input_combo", "character_combo_names", "weapon_combo_names", "predicted_avg_getmmr"]
        ].head(10).to_dict(orient="records"),
        "dropped_prediction_tables": dropped_tables,
    }
    summary_path = save_summary(summary_payload)
    exported_report_paths = export_pipeline_reports(
        cutoff_datetime=cutoff_datetime,
        training_results_df=training_results_df,
        prediction_df=prediction_df,
        position_synergy_cache_df=position_synergy_cache_df,
        absolute_score_cache_df=absolute_score_cache_df,
    )
    published_artifacts = publish_training_artifacts(
        cutoff_datetime=cutoff_datetime,
        summary_path=summary_path,
        exported_report_paths=exported_report_paths,
        prediction_table=table_name,
        position_synergy_table=position_synergy_table,
        absolute_score_table=absolute_score_table,
        collection_summary=collection_summary,
        training_results_df=training_results_df,
    )
    if published_artifacts:
        print(f"[daily-pipeline] s3 artifact summary: {published_artifacts}")


if __name__ == "__main__":
    main()
