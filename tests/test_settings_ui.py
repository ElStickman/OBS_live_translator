import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class SettingsBrowserTests(unittest.TestCase):
    def test_loading_failure_retry_and_mobile_layout(self):
        browser = next((str(path) for path in (
            Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        ) if path.exists()), None) or shutil.which("chromium")
        if not browser:
            self.skipTest("Chrome, Edge or Chromium is required")
        page = (Path(__file__).parents[1] / "translator/static/settings.html").read_text(encoding="utf-8")
        check = r"""
    const assert = (condition, message) => { if (!condition) throw Error(message); };
    (async () => {
      assert(saveTerms.disabled && saveLanguage.disabled, 'Saving enabled before loading');
      window.fetch = async () => ({ok: false, json: async () => ({error: 'Unavailable'})});
      await loadTerms(); await loadLanguageMode(); await loadSources();
      assert(saveTerms.disabled && saveLanguage.disabled && start.disabled, 'Failed loading permits save');
      assert(!refreshSources.disabled, 'Cannot retry source discovery');
      assert(termsStatus.textContent.includes('Unavailable'), 'Server error hidden');
      const devices = [{backend: 'sounddevice', device: 2, name: 'Test microphone', channels: 1, sample_rate: 48000}];
      window.fetch = async url => ({ok: true, json: async () =>
        url.includes('audio-sources') ? devices : url.includes('audio-selection') ? {backend: 'sounddevice', device: 2} : url.includes('language-mode') ? {mode: 'all'} : {terms: []}});
      await loadSources(); await loadTerms(); await loadLanguageMode();
      assert(!start.disabled && !saveTerms.disabled && !saveLanguage.disabled, 'Loaded controls remain disabled');
      assert(languageMode.value === 'all', 'Saved language not restored');
      assert(JSON.parse(source.value).device === 2 && status.textContent.includes('restored'), 'Saved microphone not restored');
      devices.splice(0, 1, {backend: 'sounddevice', device: 9, name: 'Other microphone', channels: 1, sample_rate: 48000});
      await loadSources();
      assert(start.disabled && source.selectedIndex === -1, 'Missing microphone silently replaced');
      devices.push({backend: 'sounddevice', device: 2, name: 'Test microphone', channels: 1, sample_rate: 48000});
      await loadSources();
      assert(JSON.parse(source.value).device === 2 && !start.disabled, 'Reconnected microphone not restored');
      addTerm.click();
      assert(document.activeElement === terms.querySelector('input'), 'New term did not receive focus');
      assert(document.documentElement.scrollWidth <= innerWidth, 'Page overflows mobile viewport');
      terms.querySelector('button').click();
      assert(document.activeElement === addTerm && terms.querySelector('.empty-terms'), 'Removal loses keyboard focus');
      document.body.textContent = 'SETTINGS_CHECK_PASSED';
    })().catch(error => { document.body.textContent = 'SETTINGS_CHECK_FAILED: ' + error.message; });
"""
        page = page.replace("    loadSources(); loadTerms(); loadLanguageMode();", check)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "settings.html"
            target.write_text(page, encoding="utf-8")
            result = subprocess.run([
                browser, "--headless", "--disable-gpu", "--no-first-run",
                f"--user-data-dir={directory}/profile", "--window-size=390,844",
                "--dump-dom", "--virtual-time-budget=2000", target.as_uri(),
            ], capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"<body>SETTINGS_CHECK_PASSED\s*</body>")


if __name__ == "__main__":
    unittest.main()
