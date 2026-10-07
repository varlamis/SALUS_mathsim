from __future__ import annotations

import argparse
import json
from pathlib import Path

from .uc1.analysis import export_analysis, run_analysis
from .uc1.experiments import run_matrix
from .uc1.graph import static_document
from .uc1.simulation import export_result, run_simulation
from .validation import RepositoryValidationError, validate_repository
from .handoff import build_manifest, verify_manifest


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="salus-uc1")
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--write-graph", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--output", type=Path)
    experiment = commands.add_parser("experiment")
    experiment.add_argument("--matrix", type=Path, default=Path("configs/uc1/experiments.yaml"))
    experiment.add_argument("--output", type=Path, default=Path("reports/generated/uc1/experiments"))
    analyze = commands.add_parser("analyze")
    analyze.add_argument("--design", type=Path, default=Path("configs/uc1/monte_carlo.yaml"))
    analyze.add_argument("--samples", type=int)
    analyze.add_argument("--output", type=Path, default=Path("reports/generated/uc1/monte_carlo"))
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--output", type=Path, default=Path("reports/final/UC1_artifact_manifest.json"))
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "validate":
            path = args.config if args.config.is_absolute() else root / args.config
            report = validate_repository(root, path)
            if args.write_graph:
                graph_path = root / "models/graph/uc1_graph.json"
                graph_path.write_text(json.dumps(static_document(root), indent=2, sort_keys=True) + "\n", encoding="utf-8")
                report["graph_output"] = str(graph_path.relative_to(root))
            print(json.dumps(report, indent=2))
        elif args.command == "run":
            path = args.config if args.config.is_absolute() else root / args.config
            validate_repository(root, path)
            result = run_simulation(root, path)
            destination = args.output or Path(result.documents["resolved_config"]["outputs"]["directory"])
            destination = destination if destination.is_absolute() else root / destination
            export_result(result, destination)
            print(json.dumps({"status": "completed", "canonical_hash": result.canonical_hash, "output": str(destination)}, indent=2))
        elif args.command == "experiment":
            path = args.matrix if args.matrix.is_absolute() else root / args.matrix
            result = run_matrix(root, path)
            output = args.output if args.output.is_absolute() else root / args.output
            output.mkdir(parents=True, exist_ok=True)
            (output / "experiment_comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            lines = ["# UC1 experiment comparison", "", f"Status: **{result['status']}**", "", "| Branch | Alerts | Effects | Safety violations |", "|---|---:|---:|---:|"]
            for row in result["experiments"]:
                lines.append(f"| {row['id']} | {row['alert_count']} | {row['controller_effect_count']} | {row['safety_violation_count']} |")
            (output / "experiment_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "pass" else 3
        elif args.command == "analyze":
            path = args.design if args.design.is_absolute() else root / args.design
            result = run_analysis(root, path, args.samples)
            output = args.output if args.output.is_absolute() else root / args.output
            export_analysis(result, output)
            print(json.dumps({"status": "completed", "samples": result["sample_count"], "output": str(output)}, indent=2))
        else:
            output = args.output if args.output.is_absolute() else root / args.output
            manifest = build_manifest(root, output)
            errors = verify_manifest(root, manifest)
            if errors:
                raise ValueError("manifest verification failed: " + "; ".join(errors))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"status": "valid", "artifacts": manifest["artifact_count"], "output": str(output)}, indent=2))
    except RepositoryValidationError as exc:
        print(str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
