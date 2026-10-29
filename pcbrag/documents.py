"""Loading + chunking. Markdown is split on headings, PDFs per page, logs one chunk per run."""
import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader

from pcbrag import testlogs

MAX_CHARS = 1200
OVERLAP = 200


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    doc_type: str          # datasheet / spec / test_log
    title: str = ""
    section: str = ""
    page: int = 0

    def header(self):
        where = f"p.{self.page}" if self.page else self.section
        return f"{self.source} ({where})" if where else self.source

    def to_dict(self):
        return asdict(self)


def _id(*parts):
    # azure search keys only allow letters, digits, _ - =
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:20]


def split_text(text, max_chars=MAX_CHARS, overlap=OVERLAP):
    """split on paragraphs/lines, falls back to hard cuts for very long lines"""
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    pieces, current = [], ""
    for para in re.split(r"\n\s*\n|\n(?=[-|#*\d])", text):
        if len(current) + len(para) + 1 > max_chars and current:
            pieces.append(current.strip())
            current = current[-overlap:]  # carry some context over
        current += "\n" + para
        while len(current) > max_chars:
            pieces.append(current[:max_chars].strip())
            current = current[max_chars - overlap:]
    if current.strip():
        pieces.append(current.strip())
    return pieces


def guess_type(path):
    name = path.name.lower()
    if "spec" in name or "hw_" in name:
        return "spec"
    return "datasheet"


def load_markdown(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    chunks = []
    # split into sections on "## " headings
    sections = re.split(r"\n(?=## )", text)
    for sec in sections:
        first = sec.strip().splitlines()[0] if sec.strip() else ""
        section = first.lstrip("# ").strip()
        for i, piece in enumerate(split_text(sec)):
            # prefix with title + section so a chunk like "VIN to GND: 6.5 V" still
            # knows which part it belongs to. helps retrieval a lot
            body = f"{title}\nSection: {section}\n\n{piece}" if section != title else f"{title}\n\n{piece}"
            chunks.append(Chunk(_id(path.name, section, i), body, path.name, guess_type(path),
                                title, section))
    return chunks


def load_pdf(path):
    reader = PdfReader(str(path))
    title = (reader.metadata.title if reader.metadata and reader.metadata.title else path.stem)
    chunks = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for i, piece in enumerate(split_text(text)):
            chunks.append(Chunk(_id(path.name, page_no, i), f"{title}\n\n{piece}", path.name,
                                guess_type(path), title, page=page_no))
    return chunks


def load_logs(log_dir):
    chunks = []
    for rec in testlogs.parse_dir(log_dir):
        chunks.append(Chunk(_id(rec["file"]), testlogs.summarize(rec), rec["file"], "test_log",
                            f"Test log {rec['serial']}", rec.get("result", "")))
    return chunks


def load_all(data_dir):
    data_dir = Path(data_dir)
    chunks = []
    for path in sorted(data_dir.rglob("*")):
        if path.suffix.lower() in (".md", ".txt"):
            chunks += load_markdown(path)
        elif path.suffix.lower() == ".pdf":
            chunks += load_pdf(path)
    log_dir = data_dir / "test_logs"
    if log_dir.exists():
        chunks += load_logs(log_dir)
    return chunks
