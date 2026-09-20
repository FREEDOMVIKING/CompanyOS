#!/data/data/com.termux/files/usr/bin/bash
# Repair the unpushed "full sync" commit into a clean source snapshot.
# Keeps every local file on the phone; only changes what Git tracks/stages.
set -euo pipefail

ROOT="$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
cd "$ROOT"

echo "===== COMPANYOS CLEAN SYNC REPAIR ====="
echo "REPO=$ROOT"
echo "NOTE=NO_LOCAL_FILES_ARE_DELETED"
echo "NOTE=UNPUSHED_RAW_COMMIT_IS_PRESERVED_ON_A_SAFETY_BRANCH"

[ -d .git ] || { echo "ABORT=not_git_repo"; exit 1; }

HEAD_SUBJECT="$(git log -1 --pretty=%s 2>/dev/null || true)"
HEAD_SHA="$(git rev-parse HEAD)"
echo "CURRENT_HEAD=$HEAD_SHA"
echo "CURRENT_SUBJECT=$HEAD_SUBJECT"

# Preserve the current raw local commit no matter what.
SAFETY_BRANCH="local/raw-full-sync-$STAMP"
git branch "$SAFETY_BRANCH" "$HEAD_SHA"
echo "SAFETY_BRANCH=$SAFETY_BRANCH"

# The failed run created a local commit but GitHub rejected the push.
# Move current branch back one commit while leaving all files on disk untouched.
if [ "$HEAD_SUBJECT" = "Sync full CompanyOS state before comprehensive audit" ]; then
  git reset --mixed HEAD^
  echo "RAW_SYNC_COMMIT_UNDONE_ON_CURRENT_BRANCH=PASS"
else
  echo "RAW_SYNC_COMMIT_UNDO=SKIPPED"
  echo "REASON=head_subject_not_expected"
fi

# Add a managed ignore block for local/runtime/generated material that should not
# be published as repository source. This does NOT remove any local files.
BEGIN="# BEGIN COMPANYOS LOCAL/RUNTIME EXCLUDES"
END="# END COMPANYOS LOCAL/RUNTIME EXCLUDES"
if ! grep -Fq "$BEGIN" .gitignore 2>/dev/null; then
cat >> .gitignore <<'EOF'

# BEGIN COMPANYOS LOCAL/RUNTIME EXCLUDES
# Local secrets / credentials
.env
.env.*
!.env.example
*.pem
*.key

# Python / OS / transient state
**/__pycache__/
*.py[cod]
*.log
*.pid
*.sock
*.sqlite
*.sqlite3
*.db

# CompanyOS mutable runtime
.companyos_runtime/
companyos_runtime/connectors/actions.json
companyos_runtime/connectors/executions.json
companyos_runtime/connectors/dead_letter.json
companyos_runtime/connectors/dead_letter.jsonl

# Generated operational evidence and progress ledgers
companyos_progress/
workspace/**/companyos_progress/

# Timestamped source/test/script backups; current canonical files remain tracked
**/*.v[0-9]*_backup_*
**/*_backup_[0-9]*
**/*.backup_*
**/*.bak

# Device/editor debris
*.swp
*.tmp
.DS_Store
# END COMPANYOS LOCAL/RUNTIME EXCLUDES
EOF
  echo "GITIGNORE_RUNTIME_BLOCK=ADDED"
else
  echo "GITIGNORE_RUNTIME_BLOCK=ALREADY_PRESENT"
fi

# Make the audit script non-paging if it exists.
for f in \
  "$HOME/companyos_full_github_sync_total_audit_20260920.sh" \
  "$ROOT/scripts/companyos_full_sync_audit.sh"
do
  if [ -f "$f" ]; then
    python - "$f" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text()
s=s.replace('git diff --cached --stat || true','git --no-pager diff --cached --stat || true')
p.write_text(s)
PY
    chmod +x "$f"
  fi
done
echo "AUDIT_PAGER_FIX=PASS"

# Stage the project using the new ignore rules.
git add -A -- .

# Extra safety: unstage categories that may already have been tracked before the
# ignore block. Working-tree copies remain untouched.
python - <<'PY'
from pathlib import Path
import subprocess,re

root=Path.home()/"companyos"
cp=subprocess.run(
    ["git","diff","--cached","--name-only","--diff-filter=ACMRD"],
    cwd=root,text=True,capture_output=True,check=True
)
paths=cp.stdout.splitlines()

backup_re=re.compile(r"(?:\.v\d+(?:_\d+)*_backup_|_backup_\d+|\.backup_|\.bak$)",re.I)
runtime_res=[
    re.compile(r"^\.companyos_runtime/"),
    re.compile(r"^companyos_progress/"),
    re.compile(r"^workspace/.+/companyos_progress/"),
    re.compile(r"^companyos_runtime/connectors/(?:actions|executions|dead_letter)(?:\.jsonl?|)$"),
    re.compile(r"(?:^|/)__pycache__/"),
    re.compile(r"\.(?:pyc|pyo|log|pid|sock|sqlite|sqlite3|db)$",re.I),
]
secret_name=re.compile(r"(^|/)(?:\.env(?:\.|$)|.*private.*\.(?:pem|key|json)$|credentials?(?:\.json)?$|secrets?(?:\.json)?$)",re.I)

unstage=[]
for p in paths:
    if p==".gitignore":
        continue
    if backup_re.search(p) or secret_name.search(p) or any(rx.search(p) for rx in runtime_res):
        unstage.append(p)

for p in unstage:
    subprocess.run(["git","reset","-q","HEAD","--",p],cwd=root)

print(f"UNSTAGED_LOCAL_RUNTIME_OR_BACKUP_FILES={len(unstage)}")
PY

echo "===== CLEAN STAGED SUMMARY ====="
git --no-pager diff --cached --stat
echo
echo "STAGED_FILE_COUNT=$(git diff --cached --name-only | wc -l | tr -d ' ')"

# Secret gate: report file/line/type only; never print secret values.
python - <<'PY'
from pathlib import Path
import subprocess,re,sys

root=Path.home()/"companyos"
files=subprocess.run(
    ["git","diff","--cached","--name-only","--diff-filter=ACMR"],
    cwd=root,text=True,capture_output=True,check=True
).stdout.splitlines()

patterns=[
    ("OPENAI_KEY",re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("GITHUB_TOKEN",re.compile(r"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{20,}")),
    ("PRIVATE_KEY",re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("SMTP_PASSWORD",re.compile(r"(?i)\bSMTP_PASSWORD\s*=\s*['\"]?([^\s#'\"]{8,})")),
    ("SOLANA_PRIVATE_KEY",re.compile(r"(?i)\bSOLANA_PRIVATE_KEY\s*=\s*['\"]?([^\s#'\"]{16,})")),
]

hits=[]
for rel in files:
    p=root/rel
    try:
        if not p.is_file() or p.stat().st_size>3_000_000:
            continue
        text=p.read_text(errors="ignore")
    except Exception:
        continue
    for n,line in enumerate(text.splitlines(),1):
        for kind,rx in patterns:
            if not rx.search(line):
                continue
            low=line.lower()
            if any(x in low for x in ("example","placeholder","changeme","dummy","your_key","test_key")):
                continue
            hits.append((rel,n,kind))

if hits:
    print("SECRET_GATE=BLOCK")
    for rel,n,kind in hits[:100]:
        print(f"SECRET_RISK_FILE={rel} LINE={n} TYPE={kind}")
    sys.exit(42)

print("SECRET_GATE=PASS")
print(f"STAGED_FILES_SCANNED={len(files)}")
PY

# Show a short sample so the user can sanity-check what will be committed.
echo "===== FIRST 80 STAGED PATHS ====="
git --no-pager diff --cached --name-only | sed -n '1,80p'

if git diff --cached --quiet; then
  echo "CLEAN_COMMIT=NO_CHANGES"
else
  git commit -m "Sync current CompanyOS source before comprehensive audit"
  echo "CLEAN_COMMIT=PASS"
fi

CLEAN_SHA="$(git rev-parse HEAD)"
echo "CLEAN_SHA=$CLEAN_SHA"

# Confirm the remote branch still hasn't received the failed raw commit.
BRANCH="$(git branch --show-current)"
git fetch origin "$BRANCH" >/dev/null 2>&1 || true
if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
  COUNTS="$(git rev-list --left-right --count "origin/$BRANCH...HEAD")"
  echo "REMOTE_COMPARE=$COUNTS"
fi

echo
echo "===== AUTH STATUS ====="
if command -v gh >/dev/null 2>&1 && gh auth status -h github.com >/dev/null 2>&1; then
  echo "GITHUB_CLI_AUTH=READY"
  gh auth setup-git
  echo "NEXT_COMMAND=bash ~/companyos_full_github_sync_total_audit_20260920.sh"
else
  echo "GITHUB_CLI_AUTH=NEEDED"
  echo "NEXT_1=pkg install gh -y"
  echo "NEXT_2=gh auth login --hostname github.com --git-protocol https --web"
  echo "NEXT_3=gh auth setup-git"
  echo "NEXT_4=bash ~/companyos_full_github_sync_total_audit_20260920.sh"
fi

echo "COMPANYOS_CLEAN_SYNC_REPAIR=COMPLETE"
