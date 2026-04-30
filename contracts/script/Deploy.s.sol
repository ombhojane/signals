// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {HypeScanVault} from "../src/HypeScanVault.sol";

/// @notice Deploys HypeScanVault. Reads config from environment:
///   USDC_ADDRESS       Base asset (USDC on the target chain)
///   SWAP_ROUTER_02     Uniswap V3 SwapRouter02 on the target chain
///   AGENT_ADDRESS      Address allowed to call executeTrade
///
/// Usage (local anvil fork):
///   anvil --fork-url https://mainnet.base.org
///   forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 \
///     --private-key <anvil-key> --broadcast
///
/// Usage (Base mainnet):
///   forge script script/Deploy.s.sol --rpc-url base \
///     --private-key $DEPLOYER_PK --broadcast --verify
contract Deploy is Script {
    function run() external returns (HypeScanVault vault) {
        address usdc = vm.envAddress("USDC_ADDRESS");
        address router = vm.envAddress("SWAP_ROUTER_02");
        address agent = vm.envAddress("AGENT_ADDRESS");

        vm.startBroadcast();
        vault = new HypeScanVault(IERC20(usdc), router, agent);
        vm.stopBroadcast();

        console2.log("HypeScanVault deployed at:", address(vault));
        console2.log("  asset (USDC):", usdc);
        console2.log("  router:      ", router);
        console2.log("  agent:       ", agent);
    }
}
