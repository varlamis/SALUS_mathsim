"""Command-line entry points for validating UC4 before simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .graph_builder import write_graph
from .handoff import write_artifact_manifest
from .uc4.analysis import export_monte_carlo, run_monte_carlo
from .uc4.experiments import run_experiment_matrix
from .uc4.queries import CompetencyQueryEngine, load_graph
from .uc4.simulation import export_result, run_simulation
from .validation import RepositoryValidationError, validate_repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="salus-t43")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate all UC4 contracts and cross-references")
    validate.add_argument("--config", type=Path, required=True, help="configuration path relative to repository root")
    validate.add_argument("--write-graph", action="store_true", help="write models/graph/uc4_graph.json after validation")
    run = subparsers.add_parser("run", help="validate and execute the deterministic UC4 simulation")
    run.add_argument("--config", type=Path, required=True, help="configuration path relative to repository root")
    run.add_argument("--output", type=Path, help="override the configured output directory")
    experiment = subparsers.add_parser("experiment", help="execute and compare the versioned UC4 experiment matrix")
    experiment.add_argument("--matrix", type=Path, default=Path("configs/uc4/experiments.yaml"))
    experiment.add_argument("--output", type=Path, default=Path("reports/generated/uc4/experiments"))
    analyze = subparsers.add_parser("analyze", help="run the seeded UC4 Monte Carlo and sensitivity analysis")
    analyze.add_argument("--design", type=Path, default=Path("configs/uc4/monte_carlo.yaml"))
    analyze.add_argument("--output", type=Path, default=Path("reports/generated/uc4/monte_carlo"))
    analyze.add_argument("--samples", type=int, help="test-only override of the declared sample count")
    query = subparsers.add_parser("graph-query", help="run UC4 competency queries against an exported runtime graph")
    query.add_argument("--graph", type=Path, required=True, help="runtime graph JSON")
    query.add_argument("--query", default="all", help="query name or 'all'")
    query.add_argument("--output", type=Path, help="optional JSON output path")
    manifest = subparsers.add_parser("manifest", help="generate and verify the final UC4 artifact hash manifest")
    manifest.add_argument("--output", type=Path, default=Path("reports/final/UC4_artifact_manifest.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path.cwd()
    try:
        if args.command == "validate":
            config_path = args.config if args.config.is_absolute() else root / args.config
            report, document = validate_repository(root, config_path)
            if args.write_graph:
                graph_path = root / "models" / "graph" / "uc4_graph.json"
                write_graph(document, graph_path)
                report["graph_output"] = str(graph_path.relative_to(root))
            print(json.dumps(report, indent=2))
        elif args.command == "run":
            config_path = args.config if args.config.is_absolute() else root / args.config
            result = run_simulation(root, config_path)
            configured = Path(result.documents["resolved_config"]["outputs"]["directory"])
            output = args.output or configured
            output = output if output.is_absolute() else root / output
            export_result(result, output)
            print(json.dumps({
                "status": "completed",
                "run_id": result.run_id,
                "canonical_result_sha256": result.canonical_result_hash,
                "output_directory": str(output),
            }, indent=2))
        elif args.command == "experiment":
            matrix_path = args.matrix if args.matrix.is_absolute() else root / args.matrix
            output = args.output if args.output.is_absolute() else root / args.output
            result = run_experiment_matrix(root, matrix_path, output)
            print(json.dumps({
                "status": result.status,
                "experiments": len(result.rows),
                "failures": list(result.failures),
                "output_directory": str(output),
            }, indent=2))
            if result.failures:
                return 3
        elif args.command == "analyze":
            design_path = args.design if args.design.is_absolute() else root / args.design
            output = args.output if args.output.is_absolute() else root / args.output
            result = run_monte_carlo(root, design_path, args.samples)
            export_monte_carlo(result, output)
            print(json.dumps({
                "status": "completed", "samples": len(result.samples),
                "samples_sha256": result.summary["samples_sha256"],
                "output_directory": str(output),
            }, indent=2))
        elif args.command == "manifest":
            output = args.output if args.output.is_absolute() else root / args.output
            manifest = write_artifact_manifest(root, output)
            print(json.dumps({
                "status": "valid", "artifacts": manifest["artifact_count"],
                "output": str(output),
            }, indent=2))
        else:
            graph_path = args.graph if args.graph.is_absolute() else root / args.graph
            result = CompetencyQueryEngine(load_graph(graph_path)).run(args.query)
            rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
            if args.output:
                output = args.output if args.output.is_absolute() else root / args.output
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(rendered, encoding="utf-8")
            else:
                print(rendered, end="")
    except RepositoryValidationError as exc:
        print(str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
