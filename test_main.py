"""Tests for the news-image-20261120 entry program (pure Python stdlib).

Run:  python3 -m unittest test_main -v
The program renders a 1024x1024 PNG summing up 20 November 2026 world news
and writes it to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
"""

import ast
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(REPO, "main.py")


def run_main(outdir):
    env = dict(os.environ, MAKEFUN_OUTPUT_DIR=outdir)
    return subprocess.run(
        [sys.executable, MAIN], env=env, capture_output=True, text=True, timeout=120
    )


def read_png_header(path):
    with open(path, "rb") as fh:
        data = fh.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    w, h = struct.unpack(">II", data[16:24])
    return data, w, h


class TestOutputContract(unittest.TestCase):
    def test_runs_and_writes_entry_png(self):
        outdir = tempfile.mkdtemp()
        try:
            proc = run_main(outdir)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.exists(os.path.join(outdir, "entry.png")))
        finally:
            shutil.rmtree(outdir, ignore_errors=True)

    def test_png_is_1024x1024(self):
        outdir = tempfile.mkdtemp()
        try:
            run_main(outdir)
            _, w, h = read_png_header(os.path.join(outdir, "entry.png"))
            self.assertEqual((w, h), (1024, 1024))
        finally:
            shutil.rmtree(outdir, ignore_errors=True)

    def test_png_under_1_mib_and_well_formed(self):
        outdir = tempfile.mkdtemp()
        try:
            run_main(outdir)
            path = os.path.join(outdir, "entry.png")
            size = os.path.getsize(path)
            self.assertLessEqual(size, 1048576, f"entry.png is {size} bytes")
            data, w, h = read_png_header(path)
            # every chunk parses with a valid CRC and the stream ends at IEND
            pos = 8
            seen_iend = False
            idat = b""
            while pos < len(data):
                length = struct.unpack(">I", data[pos:pos + 4])[0]
                ctype = data[pos + 4:pos + 8]
                chunk = data[pos + 8:pos + 8 + length]
                crc_stored = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
                crc_real = zlib.crc32(ctype + chunk) & 0xFFFFFFFF
                self.assertEqual(crc_stored, crc_real, f"bad CRC in {ctype}")
                if ctype == b"IDAT":
                    idat += chunk
                if ctype == b"IEND":
                    seen_iend = True
                    self.assertEqual(pos + 12 + length, len(data), "trailing bytes after IEND")
                pos += 12 + length
            self.assertTrue(seen_iend, "no IEND chunk")
            raw = zlib.decompress(idat)
            # 1024 rows of (1 filter byte + 1024*3 bytes)
            self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))
            self.assertTrue(all(raw[y * 3073] == 0 for y in range(1024)),
                            "filter byte must be 0 on every row")
        finally:
            shutil.rmtree(outdir, ignore_errors=True)

    def test_deterministic_two_runs_byte_identical(self):
        d1, d2 = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            run_main(d1)
            run_main(d2)
            b1 = open(os.path.join(d1, "entry.png"), "rb").read()
            b2 = open(os.path.join(d2, "entry.png"), "rb").read()
            self.assertEqual(hashlib.sha256(b1).hexdigest(),
                             hashlib.sha256(b2).hexdigest())
        finally:
            shutil.rmtree(d1, ignore_errors=True)
            shutil.rmtree(d2, ignore_errors=True)

    def test_stdlib_only_imports(self):
        with open(MAIN, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        allowed = {"os", "sys", "zlib", "struct", "binascii", "hashlib", "math"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0], allowed,
                                  f"non-stdlib import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                self.assertIn((node.module or "").split(".")[0], allowed,
                              f"non-stdlib import: {node.module}")


class TestFontAndText(unittest.TestCase):
    def test_font_covers_every_character_used(self):
        import main
        missing = sorted(set(main.CONTENT_TEXT) - set(main.FONT) - {"\n"})
        self.assertEqual(missing, [], f"characters with no glyph: {missing}")

    def test_wrap_never_exceeds_width(self):
        import main
        for text, scale, max_w in [
            ("CYCLONE AKVAN HITS ODISHA", 4, 380),
            ("A NUCLEAR WAR CANNOT BE WON AND MUST NEVER BE FOUGHT", 2, 440),
            ("MYANMAR GUILTY OF GENOCIDE - A FIRST FOR THE WORLD COURT", 2, 440),
        ]:
            lines = main.wrap_text(text, scale, max_w)
            for line in lines:
                self.assertLessEqual(main.text_width(line, scale), max_w,
                                     f"line too wide: {line!r}")

    def test_every_story_panel_is_drawn_not_blank(self):
        # Each named panel region must contain more than one colour:
        # background alone would mean the panel never drew.
        import main
        canvas = main.build_canvas()
        regions = {
            "masthead": (0, 0, 1024, 108),
            "hero_art": (28, 132, 600, 540),
            "hero_text": (620, 132, 996, 540),
            "summit": (28, 572, 500, 790),
            "hague": (524, 572, 996, 790),
            "bottom": (28, 812, 996, 950),
        }
        for name, (x0, y0, x1, y1) in regions.items():
            colours = set()
            for y in range(y0, y1, 7):
                for x in range(x0, x1, 7):
                    colours.add(canvas.pixel(x, y))
            self.assertGreater(len(colours), 3, f"panel {name} looks blank: {colours}")

    def test_date_is_on_the_image(self):
        import main
        canvas = main.build_canvas()
        # The masthead date band must contain dark ink pixels (text) on the
        # cream masthead: count non-background pixels in the date row.
        ink = 0
        for y in range(58, 100):
            for x in range(28, 996):
                if canvas.pixel(x, y) != main.CREAM:
                    ink += 1
        self.assertGreater(ink, 2000, "masthead date text missing")


class TestContent(unittest.TestCase):
    def test_all_six_stories_present_in_content(self):
        import main
        for needle in ["AKVAN", "GOPALPUR", "TRUMP", "XI", "PUTIN",
                        "MYANMAR", "GENOCIDE", "HAN DUCK-SOO", "SEOUL",
                        "SENSEX", "ANTHROPIC", "GTA VI", "20 NOVEMBER 2026"]:
            self.assertIn(needle, main.CONTENT_TEXT, f"missing story: {needle}")

    def test_no_forbidden_strings(self):
        import main
        for bad in ["http://", "https://", "19 NOVEMBER 2025", "LOREM"]:
            self.assertNotIn(bad, main.CONTENT_TEXT)


if __name__ == "__main__":
    unittest.main()
