from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ER_db_training import ERDBClassification
from generate_all_character_combo_predictions import BatchComboPredictor


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "reports"
PREDICTION_DIR = BASE_DIR / "predictions"
RANKPOINT_THRESHOLD = 6100


EXPERIMENTS = [
    {
        "experiment_id": "rp6100_exp_01",
        "label": "higher_lr_shallow",
        "params": {
            "n_estimators": 5000,
            "learning_rate": 0.04,
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
        "experiment_id": "rp6100_exp_02",
        "label": "deeper_balanced",
        "params": {
            "n_estimators": 7000,
            "learning_rate": 0.025,
            "max_depth": 5,
            "min_child_weight": 10,
            "reg_alpha": 0.8,
            "reg_lambda": 3.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "rp6100_exp_03",
        "label": "stronger_regularization",
        "params": {
            "n_estimators": 6000,
            "learning_rate": 0.03,
            "max_depth": 4,
            "min_child_weight": 14,
            "reg_alpha": 1.5,
            "reg_lambda": 5.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "rp6100_exp_04",
        "label": "row_col_sampling",
        "params": {
            "n_estimators": 6500,
            "learning_rate": 0.03,
            "max_depth": 4,
            "min_child_weight": 12,
            "reg_alpha": 1.0,
            "reg_lambda": 3.0,
            "subsample": 0.7,
            "colsample_bytree": 0.7,
            "early_stopping_rounds": 50,
        },
    },
    {
        "experiment_id": "rp6100_exp_05",
        "label": "lower_lr_more_trees",
        "params": {
            "n_estimators": 9000,
            "learning_rate": 0.02,
            "max_depth": 4,
            "min_child_weight": 12,
            "reg_alpha": 1.0,
            "reg_lambda": 3.5,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "early_stopping_rounds": 50,
        },
    },
]


def ensure_dirs():
    REPORT_DIR.mkdir(exist_ok=True)
    PREDICTION_DIR.mkdir(exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def build_predictor_from_trained_model(er_db, tier_key="all_tiers", max_character_num=83):
    predictor = object.__new__(BatchComboPredictor)
    predictor.conn = er_db.conn
    predictor.model = er_db.tier_models[tier_key]
    predictor.feature_names = er_db.tier_feature_columns[tier_key]
    predictor.label_encoders = er_db.tier_label_encoders[tier_key]
    predictor.character_name_map = {}
    predictor.weapon_name_map = {}
    predictor.character_profile_map = {}
    predictor.character_weapon_role_map = {}
    predictor.character_mmr_map = {}
    predictor.character_synergy_map = {}
    predictor.representative_weapon_map = {}
    predictor._load_master_maps()
    predictor._load_feature_stats()
    predictor.character_numbers_for_batch = sorted(
        character_num for character_num in predictor.character_profile_map.keys() if character_num <= max_character_num
    )
    return predictor


def build_metric_chart(summary_df):
    chart_path = REPORT_DIR / "parameter_experiments_rp6100_metrics.png"
    plot_df = summary_df.copy()
    metric_columns = ["mae", "rmse", "r2"]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, metric in zip(axes, metric_columns):
        sns.barplot(data=plot_df, x="label", y=metric, ax=ax, color="#2f855a")
        ax.set_title(metric.upper())
        ax.set_xlabel("experiment")
        ax.set_ylabel(metric)
        ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    plt.savefig(chart_path, dpi=160)
    plt.close(fig)
    return chart_path


def build_prediction_chart(prediction_summary_df):
    chart_path = REPORT_DIR / "parameter_experiments_rp6100_top_prediction.png"
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(
        data=prediction_summary_df,
        x="label",
        y="top_predicted_avg_getmmr",
        ax=ax,
        color="#d69e2e",
    )
    ax.set_title("Top predicted avg_getmmr by experiment (threshold 6100)")
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

        print(f"\nRunning {experiment_id} ({label}) with rankpoint_threshold={RANKPOINT_THRESHOLD}")
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
            rankpoint_threshold=RANKPOINT_THRESHOLD,
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

        predictor = build_predictor_from_trained_model(er_db, tier_key="all_tiers", max_character_num=83)
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

    summary_csv = REPORT_DIR / "parameter_experiments_rp6100_summary.csv"
    prediction_csv = REPORT_DIR / "parameter_experiments_rp6100_prediction_summary.csv"
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
