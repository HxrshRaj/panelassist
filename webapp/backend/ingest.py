"""
Turn user input into a submission dict, with hard limits on size.

Two entry points: pasted text fields, and an uploaded zip. The zip is never
extracted to disk - only a handful of known files are read in memory - and it
is rejected for path traversal, too many entries, an oversized or
suspiciously compressed member, or a large total uncompressed size.
"""
import io
import json
import re
import zipfile

MAX_FIELD_CHARS = 60_000
MAX_TOTAL_CHARS = 150_000
MAX_FILES_LISTED = 500
MAX_ZIP_BYTES = 2_000_000
MAX_ZIP_ENTRIES = 500
MAX_ZIP_UNCOMPRESSED = 20_000_000
MAX_MEMBER_READ = 500_000
MAX_COMPRESSION_RATIO = 100

_SKIP_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode"}


class InputError(ValueError):
    """The input is not acceptable; the message is safe to show to the user."""


def title_from_readme(readme: str, fallback: str = "Untitled submission") -> str:
    m = re.search(r"^\s*#\s+(.+?)\s*$", readme or "", re.MULTILINE)
    return (m.group(1) if m else fallback)[:120]


def _clip_check(name: str, value: str) -> str:
    value = value or ""
    if len(value) > MAX_FIELD_CHARS:
        raise InputError(f"{name} is {len(value):,} characters; the limit is {MAX_FIELD_CHARS:,}.")
    return value


def from_text(title: str, readme: str, reproduce: str = "", trajectory: str = "", files_text: str = "") -> dict:
    readme = _clip_check("README", readme)
    reproduce = _clip_check("REPRODUCE", reproduce)
    trajectory = _clip_check("Trajectory", trajectory)
    if not readme.strip():
        raise InputError("A README is required.")
    if len(readme) + len(reproduce) + len(trajectory) > MAX_TOTAL_CHARS:
        raise InputError(f"Total text is over {MAX_TOTAL_CHARS:,} characters.")
    files = [ln.strip() for ln in (files_text or "").splitlines() if ln.strip()]
    if len(files) > MAX_FILES_LISTED:
        raise InputError(f"More than {MAX_FILES_LISTED} files listed.")
    trajectory_obj = {}
    if trajectory.strip():
        try:
            trajectory_obj = json.loads(trajectory)
        except json.JSONDecodeError:
            trajectory_obj = {}
    return {
        "slug": re.sub(r"[^a-z0-9]+", "_", (title or title_from_readme(readme)).lower()).strip("_")[:60] or "submission",
        "title": (title or title_from_readme(readme))[:120],
        "readme": readme, "reproduce": reproduce,
        "manifest": {"files": files},
        "trajectory": trajectory_obj,
        "trajectory_raw": trajectory,
    }


def _safe_name(name: str) -> bool:
    if name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name):
        return False
    parts = re.split(r"[\\/]+", name)
    return ".." not in parts


def from_zip(data: bytes, title: str = "") -> dict:
    if len(data) > MAX_ZIP_BYTES:
        raise InputError(f"The zip is {len(data):,} bytes; the limit is {MAX_ZIP_BYTES:,}.")
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise InputError("That file is not a valid zip archive.")
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if len(infos) > MAX_ZIP_ENTRIES:
        raise InputError(f"The zip has {len(infos)} files; the limit is {MAX_ZIP_ENTRIES}.")
    total = 0
    for i in infos:
        if not _safe_name(i.filename):
            raise InputError("The zip contains an unsafe path and was rejected.")
        total += i.file_size
        if i.compress_size and i.file_size / max(i.compress_size, 1) > MAX_COMPRESSION_RATIO and i.file_size > 100_000:
            raise InputError("The zip contains a member with an implausible compression ratio and was rejected.")
    if total > MAX_ZIP_UNCOMPRESSED:
        raise InputError("The zip expands to more than the allowed size and was rejected.")

    names = [i.filename.replace("\\", "/") for i in infos]
    visible = [n for n in names if not (set(n.split("/")) & _SKIP_PARTS)]

    def find(target: str):
        hits = [n for n in visible if n.rsplit("/", 1)[-1].lower() == target.lower()]
        return min(hits, key=lambda n: n.count("/")) if hits else None

    def read(name):
        if not name:
            return ""
        info = zf.getinfo(next(i.filename for i in infos if i.filename.replace("\\", "/") == name))
        if info.file_size > MAX_MEMBER_READ:
            raise InputError(f"{name} is larger than {MAX_MEMBER_READ:,} bytes.")
        return zf.read(info).decode("utf-8", errors="replace")

    readme = read(find("README.md"))
    if not readme.strip():
        raise InputError("No README.md found in the zip.")
    reproduce = read(find("REPRODUCE.md")) or read(find("REPRODUCTION.md"))
    trajectory = read(find("trajectory.json"))
    files = [n for n in visible][:MAX_FILES_LISTED]
    manifest_name = find("manifest.json")
    if manifest_name:
        try:
            listed = json.loads(read(manifest_name)).get("files")
            if isinstance(listed, list):
                files = [str(f) for f in listed][:MAX_FILES_LISTED]
        except (json.JSONDecodeError, AttributeError):
            pass
    return from_text(title, readme, reproduce, trajectory, "\n".join(files))
