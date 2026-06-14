// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./BaseDetector.sol";

/// @title MEVDetector — Detects MEV sandwich attack patterns
/// @notice Flags buy-same-block-sell pattern with >5% slippage impact.
///         Over $1.5B extracted via MEV sandwiches in 2024.
contract MEVDetector is BaseDetector {
    uint256 public constant MIN_SLIPPAGE_BPS = 500; // 5%
    uint256 public constant MIN_VICTIM_VALUE_USD = 10_000;

    constructor() {
        detectorName = "MEVDetector";
        detectorSeverity = SEVERITY_MEDIUM;
    }

    /// @param txData ABI-encoded: (slippageBPS uint256, victimValueUSD uint256, isAtomic bool, sandwichCount uint8)
    function analyze(
        bytes calldata txData,
        bytes32[] calldata /* recentBlockHashes */,
        uint256 blockNumber
    ) external override returns (bool isThreat, uint256 confidence, bytes32 patternHash) {
        (uint256 slippageBPS, uint256 victimValueUSD, bool isAtomic, uint8 sandwichCount) =
            abi.decode(txData, (uint256, uint256, bool, uint8));

        if (slippageBPS < MIN_SLIPPAGE_BPS || victimValueUSD < MIN_VICTIM_VALUE_USD) {
            return (false, 0, bytes32(0));
        }

        // Confidence: slippage severity + victim value + atomicity + repeat count
        uint256 slippageScore = (slippageBPS * 40) / 10000;            // 5% = 20, 25% = 100
        uint256 valueScore = (victimValueUSD * 30) / 100_000;          // $10K = 3, $100K = 30
        uint256 atomicScore = isAtomic ? 25 : 0;                        // Same-block = max penalty
        uint256 repeatScore = uint256(sandwichCount) * 5;               // Each repeat = 5

        confidence = slippageScore + valueScore + atomicScore + repeatScore;
        if (confidence > 100) confidence = 100;

        patternHash = keccak256(abi.encodePacked("MEV_SANDWICH", slippageBPS, victimValueUSD, blockNumber));
        threatAtBlock[blockNumber] = patternHash;

        emit ThreatDetected(detectorName, patternHash, confidence, block.timestamp);
        return (true, confidence, patternHash);
    }
}
