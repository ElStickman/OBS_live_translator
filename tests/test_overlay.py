import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class OverlayTests(unittest.TestCase):
    def test_caption_animation_in_browser(self):
        browser = next((str(path) for path in (
            Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        ) if path.exists()), None) or shutil.which("chromium")
        if not browser:
            self.skipTest("Chrome, Edge or Chromium is required for the overlay check")
        overlay = (Path(__file__).parents[1] / "translator/static/overlay.html").read_text(
            encoding="utf-8"
        )
        check = r"""
    const assert = (condition, message) => { if (!condition) throw Error(message); };
    const pause = () => new Promise(resolve => setTimeout(resolve, 100));
    (async () => {
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      assert(reduced === (location.hash === '#reduce'), 'Browser motion preference was not applied');
      let data = {sequence: 1, text: 'First message', visible: true, highlights: []};
      window.fetch = async () => ({json: async () => data});
      await refresh();
      const first = caption;
      const fade = first.getAnimations().find(a => a.animationName === 'fade-caption');
      fade.pause();
      for (const [time, opacity] of [[0, 1], [4999, 1], [5000, 1], [10000, .5], [15000, 0]]) {
        fade.currentTime = time;
        assert(Math.abs(Number(getComputedStyle(first).opacity) - opacity) < .01,
          `Wrong opacity at ${time}ms`);
      }
      fade.currentTime = 10000;
      data = {...data, sequence: 2, text: 'Second'};
      await refresh();
      assert(first.textContent === 'First message', 'Interrupted typing lost text');
      assert(first.getAnimations().includes(fade), 'Moving restarted fading');
      assert(fade.currentTime === 10000, 'Moving reset lifetime');
      getComputedStyle(first).transform;
      assert(first.getAnimations().some(a => a.transitionProperty === 'transform') === !reduced,
        'Upward movement does not respect the motion preference');
      assert(first.style.transform !== 'translateY(0px)', 'Old caption did not move up');
      data = {...data, highlights: [{term: 'First', color: '#ff0000'}]};
      await refresh();
      assert(captions.children.length === 2, 'Highlight update duplicated caption');
      assert(first.querySelector('.highlight').textContent === 'First', 'Highlight lost');
      data = {...data, visible: false};
      await refresh();
      assert(captions.children.length === 2, 'API expiry removed a fading caption');
      window.fetch = async () => { throw Error('offline'); };
      await refresh();
      assert(captions.children.length === 2, 'Connection failure cleared captions');
      addCaption('Third', []);
      addCaption('Fourth', []);
      assert(captions.children.length === 3 && !first.isConnected, 'Three-caption limit failed');
      for (const item of captions.children) {
        item.getAnimations().find(a => a.animationName === 'fade-caption').finish();
      }
      for (let attempt = 0; attempt < 10 && captions.children.length; attempt++) await pause();
      assert(captions.children.length === 0 && caption === null, 'Expired captions remain');
      addCaption('Motion preference caption', []);
      if (reduced) {
        assert(caption.textContent === 'Motion preference caption' && animationFrame === null,
          'Reduced motion still animates typing');
      } else {
        assert(animationFrame !== null, 'Normal motion does not animate typing');
      }
      document.body.textContent = 'OVERLAY_CHECK_PASSED';
    })().catch(error => { document.body.textContent = 'OVERLAY_CHECK_FAILED: ' + error.message; });
"""
        overlay = overlay.replace("    setInterval(refresh, 200);\n    refresh();", check)
        for mode, flag in [("full", "--force-prefers-no-reduced-motion"),
                           ("reduce", "--force-prefers-reduced-motion")]:
            with self.subTest(motion=mode), tempfile.TemporaryDirectory() as directory:
                page = Path(directory) / "overlay.html"
                page.write_text(overlay, encoding="utf-8")
                result = subprocess.run([
                    browser, "--headless", "--disable-gpu", "--no-first-run", flag,
                    f"--user-data-dir={directory}/profile", "--dump-dom",
                    "--virtual-time-budget=2000", page.as_uri() + "#" + mode,
                ], capture_output=True, text=True, encoding="utf-8", timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertRegex(result.stdout, r"<body>OVERLAY_CHECK_PASSED\s*</body>")


if __name__ == "__main__":
    unittest.main()
