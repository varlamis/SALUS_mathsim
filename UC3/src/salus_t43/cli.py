import argparse
import json
from pathlib import Path

from .handoff import build_manifest, verify_manifest
from .uc3.analysis import export_analysis, run_analysis
from .uc3.experiments import run_matrix
from .uc3.graph import static_document
from .uc3.simulation import export_result, run_simulation
from .validation import RepositoryValidationError, validate_repository


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="salus-uc3")
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--write-graph", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--output", type=Path)
    experiment = commands.add_parser("experiment")
    experiment.add_argument("--matrix", type=Path, default=Path("configs/uc3/experiments.yaml"))
    experiment.add_argument("--output", type=Path, default=Path("reports/generated/uc3/experiments"))
    analyze = commands.add_parser("analyze")
    analyze.add_argument("--design", type=Path, default=Path("configs/uc3/monte_carlo.yaml"))
    analyze.add_argument("--samples", type=int)
    analyze.add_argument("--output", type=Path, default=Path("reports/generated/uc3/monte_carlo"))
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--output", type=Path, default=Path("reports/final/UC3_artifact_manifest.json"))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "validate":
            path = args.config if args.config.is_absolute() else root / args.config
            report = validate_repository(root, path)
            if args.write_graph:
                target = root / "models/graph/uc3_graph.json"
                target.write_text(json.dumps(static_document(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
                report["graph_output"] = str(target.relative_to(root))
            print(json.dumps(report, indent=2))
        elif args.command == "run":
            path = args.config if args.config.is_absolute() else root / args.config
            validate_repository(root, path)
            result = run_simulation(root, path)
            target = args.output or Path(result.documents["resolved_config"]["outputs"]["directory"])
            target = target if target.is_absolute() else root / target
            export_result(result, target)
            print(json.dumps({"status": "completed", "canonical_hash": result.canonical_hash, "output": str(target)}, indent=2))
        elif args.command == "experiment":
            result = run_matrix(root, args.matrix if args.matrix.is_absolute() else root / args.matrix)
            target = args.output if args.output.is_absolute() else root / args.output
            target.mkdir(parents=True, exist_ok=True)
            (target / "experiment_comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            lines = ["# UC3 experiment comparison", "", f"Status: **{result['status']}**", "", "| Branch | Alerts | Process effects | Safety violations | Pass |", "|---|---:|---:|---:|---|"]
            lines.extend(f"| {r['id']} | {r['alert_count']} | {r['process_effect_count']} | {r['safety_violation_count']} | {r['passed']} |" for r in result["experiments"])
            (target / "experiment_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "pass" else 3
        elif args.command == "analyze":
            result = run_analysis(root, args.design if args.design.is_absolute() else root / args.design, args.samples)
            target = args.output if args.output.is_absolute() else root / args.output
            export_analysis(result, target)
            print(json.dumps({"status": "completed", "samples": result["sample_count"], "output": str(target)}, indent=2))
        else:
            target = args.output if args.output.is_absolute() else root / args.output
            manifest = build_manifest(root, target)
            errors = verify_manifest(root, manifest)
            if errors:
                raise ValueError("; ".join(errors))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"status": "valid", "artifacts": manifest["artifact_count"], "output": str(target)}, indent=2))
    except (RepositoryValidationError, ValueError) as exc:
        print(str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
