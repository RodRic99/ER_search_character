from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ER_db_training import ERDBClassification
from generate_all_character_combo_predictions import BatchComboPredictor


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "eternareturn_DB" / "models"
REPORT_DIR = BASE_DIR / "reports"
PREDICTION_DIR = BASE_DIR / "predictions"


EXPERIMENTS = [
    {
        "experiment_id": "exp_01",
        "label": "baseline_light",
        "params": {
            "n_estimators": 8000,
            "learning_rate": 0.02,
            "max_depth": 5,
            "min_child_weight": 10,
            "reg_alpha": 0.5,
            "reg_lambda": 2.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "exp_02",
        "label": "shallower_regularized",
        "params": {
            "n_estimators": 6000,
            "learning_rate": 0.03,
            "max_depth": 4,
            "min_child_weight": 12,
            "reg_alpha": 1.0,
            "reg_lambda": 3.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "exp_03",
        "label": "deeper_conservative",
        "params": {
            "n_estimators": 12000,
            "learning_rate": 0.01,
            "max_depth": 6,
            "min_child_weight": 8,
            "reg_alpha": 0.0,
            "reg_lambda": 2.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "exp_04",
        "label": "more_row_sampling",
        "params": {
            "n_estimators": 9000,
            "learning_rate": 0.02,
            "max_depth": 5,
            "min_child_weight": 10,
            "reg_alpha": 0.5,
            "reg_lambda": 2.0,
            "subsample": 0.7,
            "colsample_bytree": 0.7,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "exp_05",
        "label": "strong_l2",
        "params": {
            "n_estimators": 10000,
            "learning_rate": 0.015,
            "max_depth": 5,
            "min_child_weight": 10,
            "reg_alpha": 0.5,
            "reg_lambda": 5.0,
            "subsample": 0.85,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
    },
]


def ensure_dirs():
    REPORT_DIR.mkdir(exist_ok=True)
    PREDICTION_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def build_metric_chart(summary_df):
    chart_path = REPORT_DIR / "parameter_experiment_metrics.png"
    plot_df = summary_df.copy()
    metric_columns = ["mae", "rmse", "r2"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, metric in zip(axes, metric_columns):
        sns.barplot(data=plot_df, x="label", y=metric, ax=ax, color="#2b6cb0")
        ax.set_title(metric.upper())
        ax.set_xlabel("experiment")
        ax.set_ylabel(metric)
        ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close(fig)
    return chart_path


def build_prediction_chart(prediction_summary_df):
    chart_path = REPORT_DIR / "parameter_experiment_top_prediction.png"
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(
        data=prediction_summary_df,
        x="label",
        y="top_predicted_avg_getmmr",
        ax=ax,
        color="#dd6b20",
    )
    ax.set_title("Top predicted avg_getmmr by experiment")
    ax.set_xlabel("experiment")
    ax.set_ylabel("top_predicted_avg_getmmr")
    ax.tick_params(axis="x", rotation=30)
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
    prediction_rows = []

    for experiment in EXPERIMENTS:
        experiment_id = experiment["experiment_id"]
        label = experiment["label"]
        model_params = experiment["params"]

        print(f"\nRunning {experiment_id} ({label})")
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
            model_params=model_params,
        )

        if results_df.empty:
            print(f"{experiment_id}: no results generated, skipping.")
            continue

        er_db.save_models(file_suffix=experiment_id)
        result_row = results_df.loc["all_tiers"].to_dict()
        result_row["experiment_id"] = experiment_id
        result_row["label"] = label
        result_row["model_params"] = str(model_params)
        result_rows.append(result_row)

        predictor = BatchComboPredictor(
            model_path=MODEL_DIR / f"xgb_model_all_tiers_{experiment_id}.json",
            feature_path=MODEL_DIR / f"xgb_model_all_tiers_{experiment_id}_features.csv",
            encoder_path=MODEL_DIR / f"xgb_model_all_tiers_{experiment_id}_label_encoders.json",
            max_character_num=83,
        )
        prediction_df, saved_path = predictor.predict_all_character_combinations(
            PREDICTION_DIR / f"all_character_combinations_avg_getmmr_{experiment_id}.csv"
        )
        top_row = prediction_df.iloc[0].to_dict()
        prediction_rows.append(
            {
                "experiment_id": experiment_id,
                "label": label,
                "prediction_csv": str(saved_path),
                "top_input_combo": top_row["input_combo"],
                "top_character_combo_names": top_row["character_combo_names"],
                "top_weapon_combo_names": top_row["weapon_combo_names"],
                "top_predicted_avg_getmmr": float(top_row["predicted_avg_getmmr"]),
            }
        )

    summary_df = pd.DataFrame(result_rows).sort_values("rmse", ascending=True).reset_index(drop=True)
    prediction_summary_df = pd.DataFrame(prediction_rows)

    summary_csv = REPORT_DIR / "parameter_experiment_summary.csv"
    prediction_csv = REPORT_DIR / "parameter_experiment_prediction_summary.csv"
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    prediction_summary_df.to_csv(prediction_csv, index=False, encoding="utf-8-sig")

    metric_chart = build_metric_chart(summary_df)
    prediction_chart = build_prediction_chart(prediction_summary_df)

    print(f"\nSaved summary: {summary_csv}")
    print(f"Saved prediction summary: {prediction_csv}")
    print(f"Saved metric chart: {metric_chart}")
    print(f"Saved prediction chart: {prediction_chart}")
    print("\nTop experiments by RMSE")
    print(summary_df[["experiment_id", "label", "mae", "rmse", "r2"]].to_string(index=False))
    print("\nTop prediction per experiment")
    print(prediction_summary_df.to_string(index=False))


if __name__ == "__main__":
    run()
