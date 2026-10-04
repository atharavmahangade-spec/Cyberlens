from analytics.real_data_adapter import prepare_real_dataset
from analytics.supervisory_pipeline import run_supervisory_assessment


def main():
    data = prepare_real_dataset()

    current_features = data["current_features"]

    # Use the latest assessment period as the current assessment.
    periods = (
        current_features["assessment_period"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
    )

    if len(periods) == 0:
        raise ValueError("No assessment periods found.")

    current_period = periods[-1]

    current_features = current_features[
        current_features["assessment_period"].astype(str)
        == current_period
    ].copy()

    result = run_supervisory_assessment(
        alerts=data["alerts"],
        cases=data["cases"],
        investigations=data["investigations"],
        escalations=data["escalations"],
        assets=data["assets"],
        monitoring=data["monitoring"],
        features=data["historical_features"],
        capabilities=data["capability_records"],
        assessment_id=f"REAL-{current_period}",
    )

    print()
    print("=" * 60)
    print("CYBERLENS REAL-DATA SUPERVISORY ASSESSMENT")
    print("=" * 60)

    print(f"Current assessment period: {current_period}")
    print(f"Entities: {result['entity_count']}")
    print()

    print("SIGNAL COUNTS")
    print("-" * 60)

    for signal_type, count in result["signal_counts"].items():
        print(f"{signal_type:25} {count}")

    print()
    print(f"Review queue: {len(result['review_queue'])}")
    print(f"Total signals: {len(result['signals'])}")
    print(f"Fused signals: {len(result['supervisory_signals'])}")

    print()
    print("TOP REVIEW ITEMS")
    print("-" * 60)

    for item in result["review_queue"][:10]:
        print(
            f"#{item['review_rank']} "
            f"{item['priority']:6} "
            f"{item['entity_id']} "
            f"score={item['supervisory_score']:.2f}"
        )

        print(
            f"   {item['reason']}"
        )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()