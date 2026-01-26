import unittest

from roth_conversions.ira_basis import allocate_ira_basis_pro_rata


class TestIRABasisProRata(unittest.TestCase):
    def test_frank_example(self):
        taxable, nontaxable, basis_after = allocate_ira_basis_pro_rata(
            ira_balance=175_000.0,
            basis_remaining=100_000.0,
            amount=40_000.0,
        )

        self.assertAlmostEqual(taxable, 17_142.85714285714, places=6)
        self.assertAlmostEqual(nontaxable, 22_857.14285714286, places=6)
        self.assertAlmostEqual(basis_after, 77_142.85714285714, places=6)


if __name__ == "__main__":
    unittest.main()
