// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract PoolRound {
    enum Status {
        None,
        Proposed,
        Approved,
        Funded,
        Settled,
        Cancelled
    }

    struct Round {
        bytes32 obligationDigest;
        address merchant;
        uint96 amountA;
        uint96 amountB;
        uint96 contributedA;
        uint96 contributedB;
        uint64 deadline;
        Status status;
        bool approvedA;
        bool approvedB;
        bool cancelA;
        bool cancelB;
    }

    IERC20 public immutable token;
    address public immutable memberA;
    address public immutable memberB;
    uint256 public nextRoundId = 1;
    uint256 private locked = 1;

    mapping(uint256 => Round) public rounds;
    mapping(bytes32 => bool) public consumedObligations;
    mapping(bytes32 => uint256) public activeObligationRound;

    event RoundCreated(
        uint256 indexed roundId,
        bytes32 indexed obligationDigest,
        address indexed merchant,
        uint256 amountA,
        uint256 amountB,
        uint256 deadline
    );
    event RoundApproved(uint256 indexed roundId, address indexed member);
    event Contributed(uint256 indexed roundId, address indexed member, uint256 amount);
    event Settled(uint256 indexed roundId, bytes32 indexed obligationDigest, address indexed merchant, uint256 total);
    event Cancelled(uint256 indexed roundId);
    event Refunded(uint256 indexed roundId, address indexed member, uint256 amount);

    error Unauthorized();
    error InvalidRound();
    error InvalidState();
    error InvalidTerms();
    error DuplicateAction();
    error TransferFailed();
    error ObligationAlreadyConsumed();
    error ObligationAlreadyActive();
    error Reentrancy();

    modifier onlyMember() {
        if (msg.sender != memberA && msg.sender != memberB) revert Unauthorized();
        _;
    }

    modifier nonReentrant() {
        if (locked != 1) revert Reentrancy();
        locked = 2;
        _;
        locked = 1;
    }

    constructor(IERC20 token_, address memberA_, address memberB_) {
        if (address(token_) == address(0) || memberA_ == address(0) || memberB_ == address(0) || memberA_ == memberB_) {
            revert InvalidTerms();
        }
        token = token_;
        memberA = memberA_;
        memberB = memberB_;
    }

    function createRound(bytes32 obligationDigest, address merchant, uint96 amountA, uint96 amountB, uint64 deadline)
        external
        onlyMember
        returns (uint256 roundId)
    {
        if (
            obligationDigest == bytes32(0) || merchant == address(0) || amountA == 0 || amountB == 0
                || deadline <= block.timestamp
        ) revert InvalidTerms();
        if (consumedObligations[obligationDigest]) revert ObligationAlreadyConsumed();
        if (activeObligationRound[obligationDigest] != 0) revert ObligationAlreadyActive();
        roundId = nextRoundId++;
        rounds[roundId] = Round({
            obligationDigest: obligationDigest,
            merchant: merchant,
            amountA: amountA,
            amountB: amountB,
            contributedA: 0,
            contributedB: 0,
            deadline: deadline,
            status: Status.Proposed,
            approvedA: false,
            approvedB: false,
            cancelA: false,
            cancelB: false
        });
        activeObligationRound[obligationDigest] = roundId;
        emit RoundCreated(roundId, obligationDigest, merchant, amountA, amountB, deadline);
    }

    function approveRound(uint256 roundId) external onlyMember {
        Round storage round = _round(roundId);
        if (round.status != Status.Proposed || block.timestamp > round.deadline) revert InvalidState();
        if (msg.sender == memberA) {
            if (round.approvedA) revert DuplicateAction();
            round.approvedA = true;
        } else {
            if (round.approvedB) revert DuplicateAction();
            round.approvedB = true;
        }
        emit RoundApproved(roundId, msg.sender);
        if (round.approvedA && round.approvedB) round.status = Status.Approved;
    }

    function contribute(uint256 roundId) external onlyMember nonReentrant {
        Round storage round = _round(roundId);
        if (round.status != Status.Approved || block.timestamp > round.deadline) revert InvalidState();
        uint96 amount;
        if (msg.sender == memberA) {
            if (round.contributedA != 0) revert DuplicateAction();
            amount = round.amountA;
            round.contributedA = amount;
        } else {
            if (round.contributedB != 0) revert DuplicateAction();
            amount = round.amountB;
            round.contributedB = amount;
        }
        if (!token.transferFrom(msg.sender, address(this), amount)) revert TransferFailed();
        emit Contributed(roundId, msg.sender, amount);
        if (round.contributedA == round.amountA && round.contributedB == round.amountB) {
            round.status = Status.Funded;
        }
    }

    function settle(uint256 roundId) external onlyMember nonReentrant {
        Round storage round = _round(roundId);
        if (round.status != Status.Funded || block.timestamp > round.deadline) revert InvalidState();
        if (consumedObligations[round.obligationDigest]) revert ObligationAlreadyConsumed();
        round.status = Status.Settled;
        consumedObligations[round.obligationDigest] = true;
        activeObligationRound[round.obligationDigest] = 0;
        uint256 total = uint256(round.amountA) + uint256(round.amountB);
        if (!token.transfer(round.merchant, total)) revert TransferFailed();
        emit Settled(roundId, round.obligationDigest, round.merchant, total);
    }

    function requestCancel(uint256 roundId) external onlyMember {
        Round storage round = _round(roundId);
        if (round.status != Status.Proposed && round.status != Status.Approved && round.status != Status.Funded) {
            revert InvalidState();
        }
        if (round.status == Status.Proposed && !(round.approvedA && round.approvedB)) {
            _cancel(roundId, round);
            return;
        }
        if (msg.sender == memberA) {
            if (round.cancelA) revert DuplicateAction();
            round.cancelA = true;
        } else {
            if (round.cancelB) revert DuplicateAction();
            round.cancelB = true;
        }
        if (round.cancelA && round.cancelB) {
            _cancel(roundId, round);
        }
    }

    function expire(uint256 roundId) external {
        Round storage round = _round(roundId);
        if (block.timestamp <= round.deadline || round.status == Status.Settled || round.status == Status.Cancelled) {
            revert InvalidState();
        }
        _cancel(roundId, round);
    }

    function claimRefund(uint256 roundId) external onlyMember nonReentrant {
        Round storage round = _round(roundId);
        if (round.status != Status.Cancelled) revert InvalidState();
        uint96 amount;
        if (msg.sender == memberA) {
            amount = round.contributedA;
            round.contributedA = 0;
        } else {
            amount = round.contributedB;
            round.contributedB = 0;
        }
        if (amount == 0) revert InvalidState();
        if (!token.transfer(msg.sender, amount)) revert TransferFailed();
        emit Refunded(roundId, msg.sender, amount);
    }

    function _round(uint256 roundId) internal view returns (Round storage round) {
        round = rounds[roundId];
        if (round.status == Status.None) revert InvalidRound();
    }

    function _cancel(uint256 roundId, Round storage round) internal {
        round.status = Status.Cancelled;
        activeObligationRound[round.obligationDigest] = 0;
        emit Cancelled(roundId);
    }
}
