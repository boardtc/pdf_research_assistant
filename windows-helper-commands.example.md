# Windows Helper Commands

These are example PowerShell commands that proved useful while running, checking, and troubleshooting the local PDF index on Windows.

Replace placeholder paths like `<repo-root>` and `<your-pdf-root>` with your own local paths.

## Check Current Indexed Count

```powershell
@'
import csv, pickle, zlib
from pathlib import Path

repo = Path(r'<repo-root>')
manifest_path = repo / 'manifest.csv'
index_root = repo / 'index'

with open(manifest_path, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

manifest_set = {str(Path(row['file_location']).as_posix()) for row in rows if row.get('file_location')}

indexed = set()
for p in index_root.glob('*/files.zip'):
    data = pickle.loads(zlib.decompress(p.read_bytes()))
    for file_location, status in data.items():
        if status == 'ERROR':
            continue
        normalized = str(Path(file_location).as_posix())
        if normalized in manifest_set:
            indexed.add(normalized)

print(len(indexed))
'@ | python -
```

## Check Whether Rebuild Is Still Running

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*rebuild_index.py*' } | Select-Object ProcessId, Name, CommandLine
```

## Check Recent Index File Activity

```powershell
Get-ChildItem -Recurse <repo-root>\index | Sort-Object LastWriteTime -Descending | Select-Object -First 10 FullName, LastWriteTime
```

## Find Missing PDFs From The Manifest

```powershell
@'
import csv, pickle, zlib
from pathlib import Path

manifest = Path(r'<repo-root>\manifest.csv')
index_root = Path(r'<repo-root>\index')

with open(manifest, newline='', encoding='utf-8-sig') as f:
    manifest_rows = list(csv.DictReader(f))

manifest_files = {str(Path(row['file_location']).as_posix()) for row in manifest_rows}

indexed = {}
for p in index_root.glob('*/files.zip'):
    indexed.update(pickle.loads(zlib.decompress(p.read_bytes())))

missing = sorted(
    f for f in manifest_files
    if f not in {str(Path(k).as_posix()) for k in indexed}
)
print('Missing:', len(missing))
for m in missing:
    print(m)
'@ | python -
```

## Find Streamlit And Python Processes

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|streamlit' } | Select-Object ProcessId, Name, CommandLine
```

## Stop A Stuck Process

```powershell
Stop-Process -Id <PID> -Force
```

## Rebuild The Index Explicitly

```powershell
cd <repo-root>
python rebuild_index.py
```

## Run The Streamlit UI

```powershell
cd <repo-root>
streamlit run pdf_research_assistant.py
```

## What Helped Most

- Check the terminal output, not just the Streamlit UI
- Confirm whether `rebuild_index.py` is still running
- Check the indexed count on disk
- Compare `manifest.csv` against the indexed files
- Look for duplicate or stuck Streamlit/Python processes
- Use `python rebuild_index.py` for a controlled rebuild instead of relying only on first-query indexing
