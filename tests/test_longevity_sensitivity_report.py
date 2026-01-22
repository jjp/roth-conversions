import unittest
from dataclasses import replace

from roth_conversions.config import load_inputs
from roth_conversions.models import ReportingInputs
from roth_conversions.reporting.builder import build_report
from roth_conversions.reporting.render_markdown import render_markdown


class TestLongevitySensitivityReport(unittest.TestCase):
    def test_longevity_section_renders_when_enabled(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        inputs = replace(
            inputs,
            reporting=ReportingInputs(
                value_basis=inputs.reporting.value_basis,
                objective=inputs.reporting.objective,
                longevity_sensitivity_enabled=True,
                longevity_horizons_years=(5, 10),
            ),
        )
        doc = build_report(inputs=inputs)
        md = render_markdown(doc)
        self.assertIn("## Longevity Sensitivity", md)


if __name__ == "__main__":
    unittest.main()
