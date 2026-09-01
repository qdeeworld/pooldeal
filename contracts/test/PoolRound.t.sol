// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {IERC20, PoolRound} from "../src/PoolRound.sol";

interface Vm {
    function prank(address) external;
    function warp(uint256) external;
    function expectRevert(bytes4) external;
}

contract MockUSDC is IERC20 {
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract PoolRoundTest {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address internal constant A = address(0xA11CE);
    address internal constant B = address(0xB0B);
    address internal constant MERCHANT = address(0xCAFE);
    bytes32 internal constant OBLIGATION = keccak256("signed-obligation-v1");

    MockUSDC internal usdc;
    PoolRound internal pool;

    function setUp() public {
        usdc = new MockUSDC();
        pool = new PoolRound(usdc, A, B);
        usdc.mint(A, 100);
        usdc.mint(B, 100);
        vm.prank(A);
        usdc.approve(address(pool), type(uint256).max);
        vm.prank(B);
        usdc.approve(address(pool), type(uint256).max);
    }

    function testTwoWalletApprovalExactSettlementAndReplayBlock() public {
        uint256 roundId = _createAndApprove(OBLIGATION, 25, 75);
        vm.prank(A);
        pool.contribute(roundId);
        vm.prank(B);
        pool.contribute(roundId);
        vm.prank(A);
        pool.settle(roundId);

        _assertEq(usdc.balanceOf(MERCHANT), 100, "merchant receives exact total");
        _assertTrue(pool.consumedObligations(OBLIGATION), "obligation is consumed");

        vm.prank(B);
        vm.expectRevert(PoolRound.ObligationAlreadyConsumed.selector);
        pool.createRound(OBLIGATION, MERCHANT, 25, 75, uint64(block.timestamp + 1 days));
    }

    function testExpiredPartialRoundRefundsWithoutMemory() public {
        uint256 roundId = _createAndApprove(keccak256("refund"), 25, 75);
        vm.prank(A);
        pool.contribute(roundId);
        vm.warp(block.timestamp + 2 days);
        pool.expire(roundId);
        vm.prank(A);
        pool.claimRefund(roundId);

        _assertEq(usdc.balanceOf(A), 100, "contributor independently recovers funds");
        _assertEq(usdc.balanceOf(address(pool)), 0, "contract retains no funds");
    }

    function testUnanimousCancellationRefundsBothContributors() public {
        uint256 roundId = _createAndApprove(keccak256("cancel"), 25, 75);
        vm.prank(A);
        pool.contribute(roundId);
        vm.prank(B);
        pool.contribute(roundId);
        vm.prank(A);
        pool.requestCancel(roundId);
        vm.prank(B);
        pool.requestCancel(roundId);
        vm.prank(A);
        pool.claimRefund(roundId);
        vm.prank(B);
        pool.claimRefund(roundId);

        _assertEq(usdc.balanceOf(A), 100, "member A refund");
        _assertEq(usdc.balanceOf(B), 100, "member B refund");
    }

    function testCannotContributeBeforeBothApprovals() public {
        vm.prank(A);
        uint256 roundId =
            pool.createRound(keccak256("not-approved"), MERCHANT, 25, 75, uint64(block.timestamp + 1 days));
        vm.prank(A);
        pool.approveRound(roundId);
        vm.prank(A);
        vm.expectRevert(PoolRound.InvalidState.selector);
        pool.contribute(roundId);
    }

    function _createAndApprove(bytes32 digest, uint96 amountA, uint96 amountB) internal returns (uint256 roundId) {
        vm.prank(A);
        roundId = pool.createRound(digest, MERCHANT, amountA, amountB, uint64(block.timestamp + 1 days));
        vm.prank(A);
        pool.approveRound(roundId);
        vm.prank(B);
        pool.approveRound(roundId);
    }

    function _assertEq(uint256 actual, uint256 expected, string memory reason) internal pure {
        require(actual == expected, reason);
    }

    function _assertTrue(bool value, string memory reason) internal pure {
        require(value, reason);
    }
}

