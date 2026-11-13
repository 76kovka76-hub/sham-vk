"""Local no-network checks for SKRBL Pencil compositor (Pillow regressions)."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from free_horde_test import _convert_to_pencil, _quality_gate, make_comic


def mock_image(index):
    im = Image.new("RGB", (1024,1024), (245,237,217))
    d = ImageDraw.Draw(im)
    for n in range(32):
        c=(20+(n*7)%90,30+(n*13)%90,35+(n*17)%90)
        x=(n*31+index*23)%800
        d.ellipse((x, n*23, x+175, n*23+200),fill=c)
        d.line((x,30,x+200,400), fill="black",width=6)
    d.rectangle((100,700,940,950),fill=(100+index*18,30+index*18,50+index*18))
    return im


class PencilRendererTests(unittest.TestCase):
    def test_pencil_effect_uses_supported_pillow_operations(self):
        result = _convert_to_pencil(mock_image(1))
        self.assertEqual(result.size,(696,527))
        self.assertEqual(result.mode,"RGB")

    def test_full_four_panel_compositor_no_api_calls(self):
        with patch("free_horde_test.ROOT", ROOT), patch("free_horde_test.OUT", ROOT/"test_renderer_comic.png"), patch("free_horde_test.INFO", ROOT/"test_renderer_meta.json"):
            path=ROOT/"test_renderer_comic.png"
            info=ROOT/"test_renderer_meta.json"
            try:
                result=make_comic(frame_provider=lambda i,p:
                    (i,mock_image(i),{"provider":"test-only","model":"mock"}))
                self.assertEqual(result,path)
                with Image.open(result) as im:
                    self.assertEqual(im.size,(1536,1536))
                data=json.loads(info.read_text(encoding="utf-8"))
                self.assertEqual(data["panels"],4)
            finally:
                path.unlink(missing_ok=True)
                info.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
