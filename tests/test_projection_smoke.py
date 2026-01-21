import unittest

from roth_conversions.config import load_inputs
from roth_conversions.models import Strategy
from roth_conversions.projection import project_with_tax_tracking
from roth_conversions.analysis.three_paths import run_three_paths


class TestProjectionSmoke(unittest.TestCase):
    def test_projection_runs(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        strat = Strategy("Conservative", annual_conversion=100_000, conversion_years=5, allow_32_bracket=False)
        result = project_with_tax_tracking(inputs=inputs, strategy=strat, horizon_years=25)

        self.assertEqual(len(result.yearly), 25)
        self.assertGreaterEqual(result.after_tax, 0.0)
        self.assertGreaterEqual(result.legacy, 0.0)

    def test_three_paths_runs(self):
        inputs = load_inputs("configs/retirement_config.template.toml")
        paths = run_three_paths(inputs=inputs)
        self.assertIn("after_tax", paths.path_a)
        self.assertIn("after_tax", paths.path_b)
        self.assertIn("after_tax", paths.path_c)


if __name__ == "__main__":
    unittest.main()
