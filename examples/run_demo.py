"""Demo: simulate a plant, analyze it, and print + save the results."""
from pdm_sentinel.pipeline import analyze_plant
from pdm_sentinel.report import write_html
from pdm_sentinel.simulator import simulate_plant


def main() -> None:
    data = simulate_plant(periods=500, seed=42)
    report = analyze_plant(data)

    for m in report.machines:
        print(f"{m.spec.display_name:<22} health {m.health.score:5.1f}/100  [{m.health.grade}]")

    print(f"\n{len(report.alerts)} active alert(s):")
    for a in report.alerts:
        print(f"  [{a.severity.upper():8}] {a.message}")

    write_html(report, "demo_report.html")
    print("\nHTML dashboard written to demo_report.html")


if __name__ == "__main__":
    main()
