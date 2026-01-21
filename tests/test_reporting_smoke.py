import unittest

from roth_conversions.config import load_inputs
from roth_conversions.reporting.builder import build_report
from roth_conversions.reporting.render_markdown import render_markdown


class TestReportingSmoke(unittest.TestCase):
    def test_build_and_render_markdown(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        doc = build_report(inputs=inputs)
        md = render_markdown(doc)
        self.assertIn(doc.title, md)
        self.assertIn("## Executive Summary", md)
        self.assertIn("## Three Paths", md)


if __name__ == "__main__":
    unittest.main()
