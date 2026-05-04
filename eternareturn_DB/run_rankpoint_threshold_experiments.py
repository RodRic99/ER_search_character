from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ER_db_training import ERDBClassification


BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"

BASE_THRESHOLD = 6200
THRESHOLDS = [BASE_THRESHOLD - 200, BASE_THRESHOLD - 100, BASE_THRESHOLD, BASE_THRESHOLD + 100, BASE_THRESHOLD + 200]
EXP_02_PARAMS = {
    "n_estimators": 6000,
    "learning_rate": 0.03,
    "max_depth": 4,
    "min_child_weight": 12,
    "reg_alpha": 1.0,
    "reg_lambda": 3.0,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "early_stopping_rounds": 50,
}


def ensure_dirs():
    REPORT_DIR.mkdir(exist_ok=True)


def build_threshold_chart(summary_df):
    chart_path = REPORT_DIR / "rankpoint_threshold_experiment_metrics.png"
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    metric_columns = ["mae", "rmse", "r2"]

    for ax, metric in zip(axes, metric_columns):
        sns.lineplot(
            data=summary_df,
            x="rankpoint_threshold",
            y=metric,
            marker="o",
            linewidth=2,
            ax=ax,
            color="#2b6cb0",
        )
        ax.set_title(f"{metric.upper()} by rankpoint threshold")
        ax.set_xlabel("rankpoint_threshold")
        ax.set_ylabel(metric)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close(fig)
    return chart_path


def run():
    ensure_dirs()
    er_db = ERDBClassification()
    er_db.conect_db()
    er_db.split_df_by_tier_group()

    result_rows = []

    for threshold in THRESHOLDS:
        print(f"\nRunning exp_02 threshold sweep: rankpoint_threshold={threshold}")
        results_df = er_db.train_xgb_by_tier_group(
            target_col="avg_getmmr",
            target_tier=None,
            use_time_decay=True,
            cutoff_datetime=None,
            recent_days=7,
            medium_days=14,
            recent_weight=1.0,
            medium_weight=0.5,
            old_weight=0.2,
            rankpoint_threshold=threshold,
            model_params=EXP_02_PARAMS,
        )

        if results_df.empty:
            print(f"threshold {threshold}: no results generated, skipping.")
            continue

        result_row = results_df.loc["all_tiers"].to_dict()
        result_row["experiment_id"] = f"exp_02_rp_{threshold}"
        result_row["label"] = "shallower_regularized_rankpoint_sweep"
        result_row["model_params"] = str(EXP_02_PARAMS)
        result_rows.append(result_row)

    summary_df = pd.DataFrame(result_rows).sort_values("rankpoint_threshold").reset_index(drop=True)
    summary_csv = REPORT_DIR / "rankpoint_threshold_experiment_summary.csv"
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    chart_path = build_threshold_chart(summary_df)

    print(f"\nSaved summary: {summary_csv}")
    print(f"Saved chart: {chart_path}")
    print("\nThreshold sweep results")
    print(summary_df[["rankpoint_threshold", "mae", "rmse", "r2", "rows", "recent_rows", "medium_rows", "old_rows"]].to_string(index=False))


if __name__ == "__main__":
    run()
