import unittest
import importlib.util
from pathlib import Path


def load_module_from_path(path: str, name: str = "aave_original"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestDecideLiquidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = Path(__file__).resolve().parent
        candidate = test_dir / "aave.original.py"
        if not candidate.exists():
            candidate = test_dir / "aave" / "aave.original.py"
        if not candidate.exists():
            raise FileNotFoundError("Could not find aave.original.py near tests")
        cls.module = load_module_from_path(str(candidate))

    def test_healthy_position_no_liquidation(self):
        # position_value high enough so HF >= 1
        position = 10000
        loan = 1000  # low loan -> high HF
        decision = self.module.decide_liquidation(position, loan)
        self.assertFalse(decision["should_liquidate"])
        self.assertGreaterEqual(decision["health_factor"], 1.0)
        self.assertEqual(decision["repay_amount"], 0.0)

    def test_underwater_position_triggers_liquidation(self):
        # Create a position where HF < 1
        # HF = position * LT / loan -> pick values accordingly
        position = 1000
        loan = 1000  # with LT=0.7 HF = 0.7 < 1
        decision = self.module.decide_liquidation(position, loan, close_factor=0.5, liquidation_bonus=0.10)
        self.assertTrue(decision["should_liquidate"])
        self.assertAlmostEqual(decision["health_factor"], position * self.module.liquidation_threshold / loan)
        expected_repay = loan * 0.5
        expected_collateral = expected_repay * 1.10
        self.assertAlmostEqual(decision["repay_amount"], expected_repay)
        self.assertAlmostEqual(decision["collateral_to_take"], expected_collateral)

    def test_zero_or_negative_loan_edge_cases(self):
        position = 1000
        for loan in (0, -100):
            decision = self.module.decide_liquidation(position, loan)
            self.assertFalse(decision["should_liquidate"])
            self.assertEqual(decision["repay_amount"], 0.0)
            self.assertEqual(decision["collateral_to_take"], 0.0)
            self.assertTrue(decision["health_factor"] == float("inf"))


if __name__ == "__main__":
    unittest.main()
