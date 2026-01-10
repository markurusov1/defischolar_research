import unittest
import importlib.util
from pathlib import Path


def load_module_from_path(path: str, name: str = "aave_original"):
    """Load a module from a given file path and return the module object."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestAaveOriginal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # locate the aave.original.py file next to this test file
        test_dir = Path(__file__).resolve().parent
        module_path = test_dir / "aave.original.py"
        cls.module = load_module_from_path(str(module_path))

    def test_borrow_returns_expected_amount(self):
        # For a position value of 10000 and ltv_max = 0.65 the loan should be 6500
        loan = self.module.borrow(10000)
        self.assertAlmostEqual(loan, 10000 * 0.65)

    def test_calculate_health_factor(self):
        # Use known values to compute expected health factor
        position_value = 10000
        loan = self.module.borrow(position_value)
        hf = self.module.calculate_health_factor(position_value, loan)
        expected = position_value * self.module.liquidation_threshold / loan
        self.assertAlmostEqual(hf, expected)

    def test_borrow_zero_collateral_behaviour(self):
        # Updated behavior: borrow(0) returns 0 and calculate_health_factor(0, 0) -> +inf
        loan = self.module.borrow(0)
        self.assertEqual(loan, 0)
        hf = self.module.calculate_health_factor(0, loan)
        self.assertTrue(hf == float("inf"))


if __name__ == "__main__":
    unittest.main()

