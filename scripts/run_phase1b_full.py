"""Execute Phase 1B full pipeline on the real organizer dataset."""

import sys
import tempfile
import time
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

from src.pipeline.run_phase1b import run_phase1b_pipeline  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    base_dir = Path(r"D:\New folder (2)")
    data_pack = base_dir / "datasets" / "6af3166e7b922_data_pack"

    # Use temp directory for pipeline artifact generation to operate safely within sandbox permissions
    temp_dir = Path(tempfile.gettempdir())
    output_dir = temp_dir / "phase1b_output"
    reports_dir = temp_dir / "phase1b_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("PHASE 1B — FULL ANALYTICAL PIPELINE EXECUTION (ORGANIZER DATASET)")
    print("=================================================================")
    print(f"Output directory: {output_dir}")
    print(f"Reports directory: {reports_dir}")

    summary = run_phase1b_pipeline(
        data_pack_dir=data_pack,
        output_dir=output_dir,
        reports_dir=reports_dir,
        bootstrap_iterations=1000,
        seed=42,
    )

    elapsed = round(time.time() - t0, 2)
    print("\n=================================================================")
    print(f"PIPELINE RUN COMPLETED IN {elapsed}s")
    print(f"Qualified Batters: {summary['qualified_batters']}")
    print(f"Qualified Bowlers: {summary['qualified_bowlers']}")
    print("Top 10 Batters Under Pressure (BPPS):")
    for i, name in enumerate(summary["top10_batters"], 1):
        print(f"  {i:2d}. {name}")
    print("\nTop 10 Bowlers Under Pressure (BWPS):")
    for i, name in enumerate(summary["top10_bowlers"], 1):
        print(f"  {i:2d}. {name}")
    print("=================================================================")
    print("Artifact files generated:")
    for f in output_dir.glob("*"):
        print(f"  {f.name} ({f.stat().st_size} bytes)")
    for f in reports_dir.glob("*"):
        print(f"  {f.name} ({f.stat().st_size} bytes)")

