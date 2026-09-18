#!/usr/bin/env python3
"""Search an ABAP source tree and emit file:line:code evidence.

Why not plain grep: this is comment-aware. In ABAP a full-line comment is `*`
in column 1 and an inline comment starts at `"`. That distinction decides real
verdicts:

  --skip-comments   live code only. Citing a commented-out statement as if the
                    program still did it is the classic way to produce a wrong
                    PASS.
  --only-comments   the fastest confirmation that a feature was deliberately
                    disabled rather than never written - which is the
                    difference between an N/A and a FAIL, and often between an
                    N/A and a SPEC STALE finding.

Sources are read with universal newlines so CRLF files report correct 1-based
line numbers, matching what SE38 / ADT shows.

Examples
--------
  python find_evidence.py --root "BUILD 20260911 EDITABLE" -p "ENQUEUE_" -p "DEQUEUE_"
  python find_evidence.py --root src -p "COMMIT WORK" --context 2
  python find_evidence.py --root src -p "TPAJAK" --only-comments
  python find_evidence.py --root src -p "AUTHORITY-CHECK" --json evidence.json

Output goes to stdout ASCII-safe (non-ASCII replaced) so a cp1252 console
survives it. Use --json or --out for the faithful UTF-8 version.
"""

import argparse
import json
import os
import re
import sys

DEFAULT_GLOBS = (".abap", ".txt", ".src")


def say(msg):
    sys.stdout.write(str(msg).encode("ascii", "replace").decode("ascii") + "\n")


def is_full_line_comment(line):
    return line[:1] in ("*", "#")


def strip_inline_comment(line):
    """Remove a trailing ABAP inline comment, respecting string literals."""
    in_string = False
    for i, ch in enumerate(line):
        if ch == "'":
            in_string = not in_string
        elif ch == '"' and not in_string:
            return line[:i]
    return line


def iter_files(root, exts, include_dirs=True):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        if not include_dirs:
            dirnames[:] = []
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in exts:
                yield os.path.join(dirpath, name)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="folder or single file to search")
    ap.add_argument("-p", "--pattern", action="append", required=True,
                    help="regex to search for; repeatable (OR-ed)")
    ap.add_argument("--ext", action="append", default=[],
                    help="file extension to include (default: .abap .txt .src)")
    ap.add_argument("--case-sensitive", action="store_true",
                    help="ABAP keywords are case-insensitive; default search is too")
    ap.add_argument("--skip-comments", action="store_true",
                    help="ignore full-line and inline comments (live code only)")
    ap.add_argument("--only-comments", action="store_true",
                    help="report ONLY commented-out lines")
    ap.add_argument("--context", type=int, default=0,
                    help="lines of context to include around each hit")
    ap.add_argument("--max-hits", type=int, default=400)
    ap.add_argument("--json", dest="json_out", help="write full results as UTF-8 JSON")
    ap.add_argument("--out", help="write a UTF-8 text report")
    args = ap.parse_args()

    if args.skip_comments and args.only_comments:
        say("ERROR: --skip-comments and --only-comments are mutually exclusive")
        raise SystemExit(2)

    exts = tuple(e if e.startswith(".") else "." + e for e in args.ext) or DEFAULT_GLOBS
    flags = 0 if args.case_sensitive else re.IGNORECASE
    regexes = [re.compile(p, flags) for p in args.pattern]

    hits = []
    scanned = 0
    for path in iter_files(args.root, exts):
        scanned += 1
        try:
            with open(path, "r", encoding="utf-8", errors="replace", newline=None) as fh:
                lines = fh.read().split("\n")
        except OSError as exc:
            say("WARN: cannot read %s (%s)" % (path, exc))
            continue

        for index, raw_line in enumerate(lines):
            line = raw_line.rstrip()
            commented = is_full_line_comment(line.lstrip()) or is_full_line_comment(line)
            if args.only_comments and not commented:
                continue
            haystack = line
            if args.skip_comments:
                if commented:
                    continue
                haystack = strip_inline_comment(line)
                if not haystack.strip():
                    continue
            if not any(rx.search(haystack) for rx in regexes):
                continue

            record = {
                "file": os.path.basename(path),
                "path": path,
                "line": index + 1,
                "code": line.strip(),
                "commented": bool(commented),
            }
            if args.context:
                lo = max(0, index - args.context)
                hi = min(len(lines), index + args.context + 1)
                record["context"] = [
                    {"line": n + 1, "code": lines[n].rstrip()} for n in range(lo, hi)
                ]
            hits.append(record)
            if len(hits) >= args.max_hits:
                break
        if len(hits) >= args.max_hits:
            say("NOTE: stopped at --max-hits=%d; narrow the pattern" % args.max_hits)
            break

    lines_out = []
    for h in hits:
        marker = "  [COMMENTED]" if h["commented"] else ""
        lines_out.append("%s:%d: %s%s" % (h["file"], h["line"], h["code"], marker))
        for ctx in h.get("context", []):
            if ctx["line"] != h["line"]:
                lines_out.append("        %d: %s" % (ctx["line"], ctx["code"]))

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines_out) + "\n")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"root": args.root, "patterns": args.pattern, "hits": hits},
                      fh, ensure_ascii=False, indent=2)

    for line in lines_out:
        say(line)
    say("")
    say("%d hit(s) in %d file(s) scanned." % (len(hits), scanned))
    if not hits:
        say("No match is itself evidence - but only if you searched for every")
        say("spelling the feature could have. Try synonyms before concluding N/A.")
    if args.out:
        say("text report -> %s" % args.out)
    if args.json_out:
        say("json  -> %s" % args.json_out)


if __name__ == "__main__":
    main()
