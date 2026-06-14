// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./BaseDetector.sol";

/// @title FlashLoanDetector — Detects flash loan attack patterns
/// @notice Flags multi-hop swaps with uncollateralized borrow in a single transaction.
///         Euler Finance lost $197M to this pattern in 2023.
contract FlashLoanDetector is BaseDetector {
    // Thresholds
    uint256 public constant MIN_HOP_COUNT = 3;
    uint256 public constant MIN_BORROW_USD = 1_000_000; // $1M minimum borrow
    uint256 public constant MAX_SWAP_USD = 10_000_000;   // $10M+ swap volume

    constructor() {
        detectorName = "FlashLoanDetector";
        detectorSeverity = SEVERITY_CRITICAL;
    }

    /// @param txData ABI-encoded: (hopCount uint8, borrowAmountUSD uint256, totalSwapUSD uint256, hasUncollateralized bool)
    function analyze(
        bytes calldata txData,
        bytes32[] calldata /* recentBlockHashes */,
        uint256 blockNumber
    ) external override returns (bool isThreat, uint256 confidence, bytes32 patternHash) {
        (uint8 hopCount, uint256 borrowUSD, uint256 swapUSD, bool uncollateralized) =
            abi.decode(txData, (uint8, uint256, uint256, bool));

        if (!uncollateralized || hopCount < MIN_HOP_COUNT) return (false, 0, bytes32(0));

        // Confidence scales with: hop depth + borrow size + swap volume
        uint256 hopScore = uint256(hopCount) * 15;           // 3 hops = 45, 6 hops = 90
        uint256 borrowScore = (borrowUSD * 30) / MIN_BORROW_USD;  // $1M = 30, $3M = 90
        uint256 swapScore = (swapUSD * 25) / MAX_SWAP_USD;        // $10M = 25, $50M = 125

        confidence = hopScore + borrowScore + swapScore;
        if (confidence > 100) confidence = 100;

        patternHash = keccak256(abi.encodePacked("FLASH_LOAN", hopCount, borrowUSD, swapUSD, blockNumber));
        threatAtBlock[blockNumber] = patternHash;

        emit ThreatDetected(detectorName, patternHash, confidence, block.timestamp);
        return (true, confidence, patternHash);
    }
}
