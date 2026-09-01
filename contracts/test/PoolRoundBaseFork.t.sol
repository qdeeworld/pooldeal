// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IERC20, PoolRound} from "../src/PoolRound.sol";

interface VmFork {
    function prank(address) external;
}

interface IERC20Fork is IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract PoolRoundBaseForkTest {
    VmFork internal constant vm = VmFork(address(uint160(uint256(keccak256("hevm cheat code")))));
    IERC20Fork internal constant BASE_USDC = IERC20Fork(0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913);
    address internal constant A = address(0xA11CE);
    address internal constant B = address(0xB0B);
    address internal constant MERCHANT = address(0xCAFE);
    address internal constant USDC_HOLDER = 0x4200000000000000000000000000000000000010;

    function testCanonicalBaseUsdcExactSettlement() public {
        if (block.chainid != 8453) return;

        PoolRound pool = new PoolRound(BASE_USDC, A, B);
        vm.prank(USDC_HOLDER);
        BASE_USDC.transfer(A, 25);
        vm.prank(USDC_HOLDER);
        BASE_USDC.transfer(B, 75);
        vm.prank(A);
        BASE_USDC.approve(address(pool), 25);
        vm.prank(B);
        BASE_USDC.approve(address(pool), 75);

        vm.prank(A);
        uint256 roundId =
            pool.createRound(keccak256("base-fork-obligation"), MERCHANT, 25, 75, uint64(block.timestamp + 1 days));
        vm.prank(A);
        pool.approveRound(roundId);
        vm.prank(B);
        pool.approveRound(roundId);
        vm.prank(A);
        pool.contribute(roundId);
        vm.prank(B);
        pool.contribute(roundId);
        vm.prank(A);
        pool.settle(roundId);

        require(BASE_USDC.balanceOf(MERCHANT) == 100, "canonical Base USDC settlement failed");
    }
}
