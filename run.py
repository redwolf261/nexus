"""
NEXUS Simulator — CLI Entry Point
Usage:
  python run.py --scale medium --seed 42
  python run.py --scale small --seed 123 --no-noise --validate-only
  python run.py --scale large --seed 42 --formats csv json neo4j geojson parquet
"""
from __future__ import annotations
import argparse
import logging
import sys
import time
from pathlib import Path


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("output/nexus_run.log", mode="w", encoding="utf-8"),
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NEXUS Synthetic Crime World Simulator — Karnataka State Police Datathon 2026",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Medium scale, seed 42, all formats
  python run.py --scale small            # Quick test run (~1,000 FIRs)
  python run.py --scale large --seed 7   # Large dataset, different seed
  python run.py --no-noise               # Clean data without noise injection
  python run.py --no-validate            # Skip validation (faster)
  python run.py --formats csv geojson    # Only export selected formats
        """,
    )
    parser.add_argument("--scale", choices=["small", "medium", "large", "research"],
                        default="medium", help="Simulation scale (default: medium)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output", type=str, default="output",
                        help="Output directory (default: ./output)")
    parser.add_argument("--formats", nargs="+",
                        choices=["csv", "json", "neo4j", "geojson", "parquet"],
                        default=["csv", "json", "neo4j", "geojson"],
                        help="Export formats (default: csv json neo4j geojson)")
    parser.add_argument("--no-noise",    action="store_true", help="Disable noise injection")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation checks")
    parser.add_argument("--verbose",     action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Ensure output directory exists before configuring file logging
    Path(args.output).mkdir(parents=True, exist_ok=True)
    configure_logging(args.verbose)

    logger = logging.getLogger("nexus.run")

    logger.info("=" * 70)
    logger.info("  NEXUS Synthetic Crime World Simulator")
    logger.info("  Karnataka State Police Datathon 2026 — Track 2")
    logger.info("  Author: Rivan Avinash Shetty (@redwolf261)")
    logger.info("=" * 70)
    logger.info(f"  Scale:  {args.scale}")
    logger.info(f"  Seed:   {args.seed}")
    logger.info(f"  Output: {args.output}")
    logger.info(f"  Formats: {', '.join(args.formats)}")
    logger.info(f"  Noise:  {'disabled' if args.no_noise else 'enabled'}")
    logger.info("=" * 70)

    t_start = time.time()

    try:
        # Import here so sys.path is already set
        from simulator.main import run_simulation

        run_simulation(
            scale=args.scale,
            seed=args.seed,
            output_dir=args.output,
            export_csv="csv" in args.formats,
            export_json="json" in args.formats,
            export_neo4j="neo4j" in args.formats,
            export_geojson="geojson" in args.formats,
            export_parquet="parquet" in args.formats,
            enable_noise=not args.no_noise,
            validate=not args.no_validate,
        )

    except KeyboardInterrupt:
        logger.warning("Simulation interrupted by user.")
        return 1
    except Exception as e:
        logger.exception(f"Simulation failed: {e}")
        return 1

    elapsed = time.time() - t_start
    logger.info(f"[DONE] Total runtime: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    logger.info(f"       Output directory: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
