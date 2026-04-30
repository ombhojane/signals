// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC4626, IERC20} from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    function exactInputSingle(ExactInputSingleParams calldata params)
        external
        payable
        returns (uint256 amountOut);
}

/// @title SignalsVault
/// @notice ERC-4626 vault whose USDC is traded on Uniswap V3 by an AI agent.
///         Every trade emits the keccak256 hash of the LLM reasoning and its
///         confidence score, creating a verifiable on-chain decision log.
contract SignalsVault is ERC4626, Ownable {
    using SafeERC20 for IERC20;

    ISwapRouter public immutable swapRouter;
    address public agent;
    bool public positionOpen;

    event TradeExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        bytes32 indexed reasoningHash,
        uint8 confidence,
        uint256 timestamp
    );
    event AgentChanged(address indexed oldAgent, address indexed newAgent);

    error NotAgent();
    error PositionCurrentlyOpen();
    error ZeroAddress();

    modifier onlyAgent() {
        if (msg.sender != agent) revert NotAgent();
        _;
    }

    constructor(IERC20 usdc, address _swapRouter, address _agent)
        ERC4626(usdc)
        ERC20("Signals Vault Share", "sVAULT")
        Ownable(msg.sender)
    {
        if (_swapRouter == address(0) || _agent == address(0)) revert ZeroAddress();
        swapRouter = ISwapRouter(_swapRouter);
        agent = _agent;
    }

    function setAgent(address newAgent) external onlyOwner {
        if (newAgent == address(0)) revert ZeroAddress();
        emit AgentChanged(agent, newAgent);
        agent = newAgent;
    }

    /// @notice Agent executes a swap on Uniswap V3 and logs the AI reasoning.
    /// @dev Position state auto-flips:
    ///      - tokenIn == asset() → opening a position
    ///      - tokenOut == asset() → closing back to base asset
    function executeTrade(
        address tokenIn,
        address tokenOut,
        uint24 poolFee,
        uint256 amountIn,
        uint256 amountOutMinimum,
        bytes32 reasoningHash,
        uint8 confidence
    ) external onlyAgent returns (uint256 amountOut) {
        address baseAsset = asset();

        IERC20(tokenIn).forceApprove(address(swapRouter), amountIn);

        amountOut = swapRouter.exactInputSingle(
            ISwapRouter.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: poolFee,
                recipient: address(this),
                amountIn: amountIn,
                amountOutMinimum: amountOutMinimum,
                sqrtPriceLimitX96: 0
            })
        );

        if (tokenOut == baseAsset) {
            positionOpen = false;
        } else if (tokenIn == baseAsset) {
            positionOpen = true;
        }

        emit TradeExecuted(
            tokenIn, tokenOut, amountIn, amountOut, reasoningHash, confidence, block.timestamp
        );
    }

    /// @dev Deposits and withdrawals are gated on positionOpen to keep
    ///      totalAssets() honest without a price oracle. Users transact only
    ///      when the vault is 100% USDC.
    function _deposit(address caller, address receiver, uint256 assets, uint256 shares)
        internal
        override
    {
        if (positionOpen) revert PositionCurrentlyOpen();
        super._deposit(caller, receiver, assets, shares);
    }

    function _withdraw(
        address caller,
        address receiver,
        address owner_,
        uint256 assets,
        uint256 shares
    ) internal override {
        if (positionOpen) revert PositionCurrentlyOpen();
        super._withdraw(caller, receiver, owner_, assets, shares);
    }
}
