import subprocess
import os
import sys

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def get_commit_message(filepath):
    norm = filepath.replace("\\", "/")
    filename = os.path.basename(norm)
    
    if norm.startswith("datasets/"):
        if "LICENSE" in filename:
            league = norm.split("/")[1].replace("_male_json", "").replace("_json", "").upper()
            return f"docs(dataset): add Cricsheet {league} license and attribution"
        elif "README" in filename:
            league = norm.split("/")[1].replace("_male_json", "").replace("_json", "").upper()
            return f"docs(dataset): add Cricsheet {league} source documentation and README"
        elif "Problem Statement" in filename or "6af3166e7b922_data_pack" in norm:
            return "docs(dataset): add SupeRR Selector Season 2 problem statement document"
        else:
            return f"docs(dataset): add {filename}"
            
    elif norm.startswith("scripts/"):
        return f"ci(scripts): add {filename} validation and automation script"
        
    elif norm.startswith(".agents/teamwork/"):
        parts = norm.split("/")
        agent = parts[2] if len(parts) > 2 else "teamwork"
        return f"chore(teamwork): record {agent} {filename} task artifact"
        
    else:
        return f"chore: update {filename}"

def main():
    rc, out, err = run_cmd("git status -s -u")
    if rc != 0:
        print(f"Error getting git status: {err}")
        sys.exit(1)

    lines = out.split("\n")
    files_to_commit = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Format is ' M file' or '?? file' or '?? "file with spaces"'
        status = line[:2].strip()
        filepath = line[3:].strip().strip('"')
        if filepath:
            files_to_commit.append(filepath)

    print(f"Found {len(files_to_commit)} uncommitted files.")
    committed_count = 0
    for idx, f in enumerate(files_to_commit, 1):
        msg = get_commit_message(f)
        print(f"[{idx}/{len(files_to_commit)}] Committing {f} -> {msg}")
        
        # Git add
        rc, _, err = run_cmd(f'git add "{f}"')
        if rc != 0:
            print(f"Failed to add {f}: {err}")
            continue
            
        # Git commit
        rc, out_c, err = run_cmd(f'git commit -m "{msg}"')
        if rc != 0:
            print(f"Failed to commit {f}: {err} | {out_c}")
            continue
            
        committed_count += 1

    print(f"\nSuccessfully committed {committed_count} of {len(files_to_commit)} files separately.")

if __name__ == "__main__":
    main()

