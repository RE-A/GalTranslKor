"""Scene TXT file plugin that preserves every source line.

Each physical line becomes one GalTransl entry in original order. Lines that
should not be translated keep an empty message (GalTransl skips those) and are
written back byte-for-byte; translatable lines keep their surrounding frame
(indentation, speaker brackets, dialogue quotes, line ending) outside the text
sent to the model.
"""
import re

from GalTransl import LOGGER
from GalTransl.GTPlugin import GFilePlugin

FRAME_KEY = "_scene_line"
QUOTES = {"「": "」", "『": "』", "（": "）"}
BOMS = ((b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16"))


def decode(data: bytes, encoding: str = "auto"):
    """Return (text, codec, has_bom)."""
    if encoding != "auto":
        return data.decode(encoding), encoding, False
    for bom, codec in BOMS:
        if data.startswith(bom):
            return data.decode(codec), codec, True
    for codec in ("utf-8", "cp932"):
        try:
            return data.decode(codec), codec, False
        except UnicodeDecodeError:
            continue
    raise ValueError("cannot detect encoding; set inputEncoding (e.g. cp932)")


def parse_lines(text: str, speaker_patterns, skip_patterns, strip_quotes=True) -> list:
    entries = []
    for index, raw in enumerate(text.splitlines(keepends=True), 1):
        body = raw.rstrip("\r\n")
        frame = {"eol": raw[len(body):]}
        entry = {"index": index}
        if any(p.search(body) for p in skip_patterns):
            frame["raw"] = body
            entry["message"] = ""
            entry[FRAME_KEY] = frame
            entries.append(entry)
            continue
        pre, mid, content = "", "", body
        for pattern in speaker_patterns:
            match = pattern.match(body)
            if match and match.group("name").strip():
                groups = match.groupdict()
                pre, mid, content = groups.get("pre") or "", groups.get("mid") or "", groups["text"]
                entry["name"] = match.group("name")
                break
        stripped = content.strip()
        lead = content[:len(content) - len(content.lstrip())]
        trail = content[len(content.rstrip()):]
        opening = closing = ""
        # Unnamed quoted lines keep their brackets so the model still sees dialogue.
        if strip_quotes and "name" in entry and len(stripped) >= 2 and QUOTES.get(stripped[0]) == stripped[-1] \
                and stripped[-1] not in stripped[1:-1]:
            opening, closing, stripped = stripped[0], stripped[-1], stripped[1:-1]
        frame.update(pre=pre, mid=mid, lead=lead + opening, trail=closing + trail)
        entry["message"] = stripped
        entry[FRAME_KEY] = frame
        entries.append(entry)
    return entries


def render_lines(entries: list) -> str:
    out = []
    for item in entries:
        frame = item[FRAME_KEY]
        if "raw" in frame:
            out.append(frame["raw"] + frame["eol"])
            continue
        name = item.get("name", "")
        out.append(f"{frame['pre']}{name}{frame['mid']}{frame['lead']}{item['message']}{frame['trail']}{frame['eol']}")
    return "".join(out)


class file_plugin(GFilePlugin):
    def gtp_init(self, plugin_conf: dict, project_conf: dict):
        settings = plugin_conf["Settings"]
        self.pname = plugin_conf["Core"].get("Name", "")
        self.input_encoding = settings.get("inputEncoding", "auto")
        self.output_encoding = settings.get("outputEncoding", "auto")
        self.strip_quotes = bool(settings.get("stripQuotes", True))
        self.speaker_patterns = [re.compile(p) for p in settings.get("speakerPatterns", []) or []]
        for pattern in self.speaker_patterns:
            if not {"name", "text"} <= set(pattern.groupindex):
                raise ValueError(f"speakerPatterns needs name/text groups: {pattern.pattern}")
        self.skip_patterns = [re.compile(p) for p in settings.get("skipPatterns", []) or []]
        LOGGER.debug(f"[{self.pname}] encoding {self.input_encoding} -> {self.output_encoding}")

    def load_file(self, file_path: str) -> list:
        if not file_path.lower().endswith(".txt"):
            raise TypeError("only .txt scene files are supported")
        with open(file_path, "rb") as f:
            text, codec, has_bom = decode(f.read(), self.input_encoding)
        entries = parse_lines(text, self.speaker_patterns, self.skip_patterns, self.strip_quotes)
        if entries:
            entries[0][FRAME_KEY]["source_codec"] = codec
            entries[0][FRAME_KEY]["source_bom"] = has_bom
        return entries

    def _codec(self, entries):
        if self.output_encoding != "auto":
            return self.output_encoding
        first = entries[0][FRAME_KEY] if entries else {}
        if first.get("source_codec") == "utf-16":
            return "utf-16"
        return "utf-8-sig" if first.get("source_bom") else "utf-8"

    def save_file(self, file_path: str, transl_json: list):
        # newline="" keeps the original CRLF/LF exactly as captured per line.
        with open(file_path, "w", encoding=self._codec(transl_json), newline="") as f:
            f.write(render_lines(transl_json))

    def gtp_final(self):
        pass
