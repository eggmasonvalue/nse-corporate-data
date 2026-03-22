import subprocess
from pathlib import Path
import sys

def run_command(cmd, cwd=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error executing command:\n{result.stderr}")
        sys.exit(result.returncode)
    print(result.stdout)


def main():
    root_dir = Path(__file__).parent.parent
    samples_dir = root_dir / "samples"
    samples_dir.mkdir(exist_ok=True)

    # 1. Fetch Further Issues (10-03-2026 to 21-03-2026) fully enriched
    print("Fetching Further Issues (10-Mar to 21-Mar)...")
    run_command(
        [
            "uv",
            "run",
            "nse-corporate-data",
            "further-issues",
            "fetch",
            "--from-date",
            "10-03-2026",
            "--to-date",
            "21-03-2026",
            "--enrich",
            "market-data",
            "--enrich",
            "industry",
            "--enrich",
            "xbrl",
        ],
        cwd=samples_dir,
    )

    # 2. Refine Further Issues
    print("Refining Further Issues...")
    run_command(
        ["uv", "run", "nse-corporate-data", "further-issues", "refine", "--category", "pref"],
        cwd=samples_dir,
    )
    run_command(
        ["uv", "run", "nse-corporate-data", "further-issues", "refine", "--category", "qip"],
        cwd=samples_dir,
    )

    # 3. Fetch Insider Trading (21-03-2026) fully enriched
    print("Fetching Insider Trading (21-Mar)...")
    run_command(
        [
            "uv",
            "run",
            "nse-corporate-data",
            "insider-trading",
            "fetch",
            "--from-date",
            "21-03-2026",
            "--to-date",
            "21-03-2026",
            "--enrich",
            "market-data",
            "--enrich",
            "industry",
            "--enrich",
            "xbrl",
        ],
        cwd=samples_dir,
    )

    # 4. Refine Insider Trading (market preset)
    print("Refining Insider Trading...")
    run_command(
        ["uv", "run", "nse-corporate-data", "insider-trading", "refine", "--preset", "market"],
        cwd=samples_dir,
    )
    
    print("Sample generation complete.")

if __name__ == "__main__":
    main()
