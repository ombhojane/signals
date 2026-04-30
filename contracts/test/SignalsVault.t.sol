// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, console2} from "forge-std/Test.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SignalsVault} from "../src/SignalsVault.sol";

/// @notice Tests run against a Base mainnet fork so they exercise real
///         Uniswap V3 liquidity instead of mocks.
contract SignalsVaultTest is Test {
    // Base mainnet addresses
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant SWAP_ROUTER_02 = 0x2626664c2603336E57B271c5C0b26F421741e481;
    uint24 constant POOL_FEE_500 = 500; // WETH/USDC 0.05% pool

    SignalsVault vault;
    address owner = makeAddr("owner");
    address agent = makeAddr("agent");
    address alice = makeAddr("alice");
    address bob = makeAddr("bob");

    bytes32 constant REASONING_HASH = keccak256("LLM said BUY WETH at $2256, confidence 82");

    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("base"));

        vm.prank(owner);
        vault = new SignalsVault(IERC20(USDC), SWAP_ROUTER_02, agent);

        // Fund Alice with 10,000 USDC
        deal(USDC, alice, 10_000 * 1e6);
        // Fund Bob with 5,000 USDC for multi-user tests
        deal(USDC, bob, 5_000 * 1e6);
    }

    // ─────────────────────────────────────────────────────────────
    // Constructor + config
    // ─────────────────────────────────────────────────────────────

    function test_Constructor_SetsState() public view {
        assertEq(address(vault.asset()), USDC);
        assertEq(address(vault.swapRouter()), SWAP_ROUTER_02);
        assertEq(vault.agent(), agent);
        assertEq(vault.owner(), owner);
        assertEq(vault.positionOpen(), false);
    }

    function test_SetAgent_OnlyOwner() public {
        address newAgent = makeAddr("newAgent");

        vm.prank(alice);
        vm.expectRevert();
        vault.setAgent(newAgent);

        vm.prank(owner);
        vault.setAgent(newAgent);
        assertEq(vault.agent(), newAgent);
    }

    // ─────────────────────────────────────────────────────────────
    // Deposit / withdraw (idle state)
    // ─────────────────────────────────────────────────────────────

    function test_Deposit_WhenIdle_MintsSharesOneToOne() public {
        uint256 amount = 1_000 * 1e6;

        vm.startPrank(alice);
        IERC20(USDC).approve(address(vault), amount);
        uint256 shares = vault.deposit(amount, alice);
        vm.stopPrank();

        assertEq(shares, amount, "shares == assets on empty vault");
        assertEq(vault.balanceOf(alice), shares);
        assertEq(vault.totalAssets(), amount);
    }

    function test_Withdraw_WhenIdle_ReturnsUsdc() public {
        uint256 amount = 1_000 * 1e6;

        vm.startPrank(alice);
        IERC20(USDC).approve(address(vault), amount);
        vault.deposit(amount, alice);

        uint256 balBefore = IERC20(USDC).balanceOf(alice);
        vault.withdraw(amount, alice, alice);
        uint256 balAfter = IERC20(USDC).balanceOf(alice);
        vm.stopPrank();

        assertEq(balAfter - balBefore, amount);
        assertEq(vault.balanceOf(alice), 0);
    }

    // ─────────────────────────────────────────────────────────────
    // executeTrade: access control + position state
    // ─────────────────────────────────────────────────────────────

    function test_ExecuteTrade_RevertsIfNotAgent() public {
        _depositAs(alice, 1_000 * 1e6);

        vm.prank(alice);
        vm.expectRevert(SignalsVault.NotAgent.selector);
        vault.executeTrade(USDC, WETH, POOL_FEE_500, 100 * 1e6, 0, REASONING_HASH, 82);
    }

    function test_ExecuteTrade_OpensPosition_UsdcToWeth() public {
        _depositAs(alice, 1_000 * 1e6);

        uint256 amountIn = 500 * 1e6;
        uint256 wethBefore = IERC20(WETH).balanceOf(address(vault));

        vm.prank(agent);
        uint256 out = vault.executeTrade(USDC, WETH, POOL_FEE_500, amountIn, 0, REASONING_HASH, 82);

        assertGt(out, 0, "received WETH");
        assertEq(IERC20(WETH).balanceOf(address(vault)) - wethBefore, out);
        assertTrue(vault.positionOpen(), "position should be open");
    }

    function test_ExecuteTrade_ClosesPosition_WethToUsdc() public {
        _depositAs(alice, 1_000 * 1e6);

        // Open position: USDC → WETH
        vm.prank(agent);
        uint256 wethOut =
            vault.executeTrade(USDC, WETH, POOL_FEE_500, 500 * 1e6, 0, REASONING_HASH, 82);
        assertTrue(vault.positionOpen());

        // Close position: WETH → USDC
        vm.prank(agent);
        uint256 usdcOut =
            vault.executeTrade(WETH, USDC, POOL_FEE_500, wethOut, 0, REASONING_HASH, 82);

        assertGt(usdcOut, 0, "received USDC");
        assertEq(vault.positionOpen(), false, "position should be closed");
    }

    // ─────────────────────────────────────────────────────────────
    // Deposit/withdraw blocked while position is open
    // ─────────────────────────────────────────────────────────────

    function test_Deposit_RevertsWhenPositionOpen() public {
        _depositAs(alice, 1_000 * 1e6);

        vm.prank(agent);
        vault.executeTrade(USDC, WETH, POOL_FEE_500, 500 * 1e6, 0, REASONING_HASH, 82);

        vm.startPrank(bob);
        IERC20(USDC).approve(address(vault), 100 * 1e6);
        vm.expectRevert(SignalsVault.PositionCurrentlyOpen.selector);
        vault.deposit(100 * 1e6, bob);
        vm.stopPrank();
    }

    function test_Withdraw_RevertsWhenPositionOpen() public {
        _depositAs(alice, 1_000 * 1e6);

        vm.prank(agent);
        vault.executeTrade(USDC, WETH, POOL_FEE_500, 500 * 1e6, 0, REASONING_HASH, 82);

        vm.prank(alice);
        vm.expectRevert(SignalsVault.PositionCurrentlyOpen.selector);
        vault.withdraw(100 * 1e6, alice, alice);
    }

    // ─────────────────────────────────────────────────────────────
    // Event emission
    // ─────────────────────────────────────────────────────────────

    function test_ExecuteTrade_EmitsReasoningHashAndConfidence() public {
        _depositAs(alice, 1_000 * 1e6);

        vm.expectEmit(true, true, true, false, address(vault));
        emit SignalsVault.TradeExecuted(USDC, WETH, 500 * 1e6, 0, REASONING_HASH, 82, 0);

        vm.prank(agent);
        vault.executeTrade(USDC, WETH, POOL_FEE_500, 500 * 1e6, 0, REASONING_HASH, 82);
    }

    // ─────────────────────────────────────────────────────────────
    // Full lifecycle
    // ─────────────────────────────────────────────────────────────

    function test_FullLifecycle_DepositTradeWithdraw() public {
        uint256 amount = 1_000 * 1e6;

        // 1. Alice deposits 1,000 USDC
        _depositAs(alice, amount);
        assertEq(vault.balanceOf(alice), amount);

        // 2. Agent opens position: 500 USDC → WETH
        vm.prank(agent);
        uint256 wethOut =
            vault.executeTrade(USDC, WETH, POOL_FEE_500, 500 * 1e6, 0, REASONING_HASH, 82);

        // 3. Agent closes position: WETH → USDC
        vm.prank(agent);
        vault.executeTrade(WETH, USDC, POOL_FEE_500, wethOut, 0, REASONING_HASH, 82);

        // 4. Alice withdraws her full share
        uint256 balBefore = IERC20(USDC).balanceOf(alice);
        uint256 shares = vault.balanceOf(alice);
        vm.prank(alice);
        vault.redeem(shares, alice, alice);
        uint256 received = IERC20(USDC).balanceOf(alice) - balBefore;

        // Expect within ~1% of original (lost to swap fees on 2 round-trip swaps)
        assertGt(received, (amount * 99) / 100, "lost more than 1% to fees");
        assertEq(vault.balanceOf(alice), 0);
        assertEq(vault.positionOpen(), false);
    }

    // ─────────────────────────────────────────────────────────────
    // Helpers
    // ─────────────────────────────────────────────────────────────

    function _depositAs(address user, uint256 amount) internal {
        vm.startPrank(user);
        IERC20(USDC).approve(address(vault), amount);
        vault.deposit(amount, user);
        vm.stopPrank();
    }
}
