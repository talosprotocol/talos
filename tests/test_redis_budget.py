
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal
from app.domain.budgets.service import BudgetService, BudgetExceededError

class TestRedisBudgetService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.redis = MagicMock()
        self.redis.register_script = MagicMock()
        
        # Mock Scripts
        self.mock_reserve = AsyncMock()
        self.mock_settle = AsyncMock()
        
        # register_script returns the callable script object
        def register_side_effect(script):
            if "local limit_team" in script:
                return self.mock_reserve
            return self.mock_settle
            
        self.redis.register_script.side_effect = register_side_effect
        
        self.service = BudgetService(self.redis)

    async def test_reserve_success(self):
        # Setup
        self.mock_reserve.return_value = [1, "OK", 0] # Allowed
        
        # Execute
        headers = await self.service.reserve(
            request_id="req1",
            team_id="team1",
            key_id="key1",
            budget_mode="hard",
            estimate_usd=Decimal("0.1"),
            limit_usd_team=Decimal("100"),
            limit_usd_key=Decimal("10"),
            overdraft_usd=Decimal("0")
        )
        
        # Verify
        self.mock_reserve.assert_called_once()
        call_kwargs = self.mock_reserve.call_args.kwargs
        args = call_kwargs['args']
        # Args: limit_team, limit_key, cost, ttl
        self.assertEqual(args[0], 100.0)
        self.assertEqual(args[1], 10.0)
        self.assertEqual(args[2], 0.1)
        
        # Verify headers
        self.assertEqual(headers["X-Talos-Budget-Remaining-Usd"], "10.000000") # Min limit is 10

    async def test_reserve_exceeded_hard(self):
        # Setup
        self.mock_reserve.return_value = [0, "Team Limit Exceeded", 100.1] 
        
        # Execute & Verify
        with self.assertRaises(BudgetExceededError):
            await self.service.reserve(
                request_id="req1",
                team_id="team1",
                key_id="key1",
                budget_mode="hard",
                estimate_usd=Decimal("0.1"),
                limit_usd_team=Decimal("10"),
                limit_usd_key=Decimal("100"),
                overdraft_usd=Decimal("0")
            )

    async def test_reserve_warn_mode(self):
        # Setup
        self.mock_reserve.return_value = [0, "Team Limit Exceeded", 100.1]
        
        # Execute
        headers = await self.service.reserve(
            request_id="req1",
            team_id="team1",
            key_id="key1",
            budget_mode="warn",
            estimate_usd=Decimal("0.1"),
            limit_usd_team=Decimal("10"),
            limit_usd_key=Decimal("100"),
            overdraft_usd=Decimal("0")
        )
        
        # Verify call used infinite limits
        call_kwargs = self.mock_reserve.call_args.kwargs
        args = call_kwargs['args']
        self.assertEqual(args[0], 999999999) # Team Limit Infinite
        self.assertEqual(args[1], 999999999)

        # Verify headers returned despite failure
        self.assertEqual(headers["X-Talos-Budget-Mode"], "warn")

    async def test_settle(self):
        await self.service.settle(
            request_id="req1",
            team_id="team1",
            key_id="key1",
            estimate_usd=Decimal("0.1"),
            actual_cost_usd=Decimal("0.05")
        )
        self.mock_settle.assert_called_once()
        args = self.mock_settle.call_args.kwargs['args']
        self.assertEqual(args[0], 0.1)  # Reserved
        self.assertEqual(args[1], 0.05) # Actual

if __name__ == '__main__':
    unittest.main()
