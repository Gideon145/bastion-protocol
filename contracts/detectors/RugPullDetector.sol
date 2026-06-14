// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./BaseDetector.sol";

/// @title RugPullDetector — Detects rug pull / liquidity removal patterns
/// @notice Flags liquidity removal >90% within 24h of large inflow.
///         $3.6B lost to rug pulls in 2023 alone.
contract RugPullDetector is BaseDetector {
    uint256 public constant MIN_LIQUIDITY_REMOVAL_BPS = 9000; // 90%
    uint256 public constant MIN_INFLOW_USD = 100_000;
    uint256 public constant MAX_WINDOW = 24 hours;

    mapping(address => uint256) public lastLargeInflow;   // token -> timestamp
    mapping(address => uint256) public inflowAmount;       // token -> USD amount

    constructor() {
        detectorName = "RugPullDetector";
        detectorSeverity = SEVERITY_HIGH;
    }

    /// @param txData ABI-encoded: (token address, liquidityRemovedBPS uint256, inflowUSDAmount uint256, hoursSinceInflow uint256)
    function analyze(
        bytes calldata txData,
        bytes32[] calldata /* recentBlockHashes */,
        uint256 blockNumber
    ) external override returns (bool isThreat, uint256 confidence, bytes32 patternHash) {
        (address token, uint256 removalBPS, uint256 inflowUSD, uint256 secondsSinceInflow) =
            abi.decode(txData, (address, uint256, uint256, uint256));

        if (removalBPS < MIN_LIQUIDITY_REMOVAL_BPS) return (false, 0, bytes32(0));
        if (inflowUSD < MIN_INFLOW_USD) return (false, 0, bytes32(0));

        // Update tracking
        lastLargeInflow[token] = block.timestamp;
        inflowAmount[token] = inflowUSD;

        // Confidence: removal severity + inflow size + time proximity
        uint256 removalScore = (removalBPS * 60) / 10000;           // 90% = 54, 100% = 60
        uint256 inflowScore = (inflowUSD * 25) / MIN_INFLOW_USD;    // $100K = 25, $1M = 250
        uint256 timeScore = secondsSinceInflow < 1 hours ? 30 :
                           (secondsSinceInflow < 6 hours ? 20 :
                           (secondsSinceInflow < 12 hours ? 10 : 0));

        confidence = removalScore + inflowScore + timeScore;
        if (confidence > 100) confidence = 100;

        patternHash = keccak256(abi.encodePacked("RUG_PULL", token, removalBPS, secondsSinceInflow, blockNumber));
        threatAtBlock[blockNumber] = patternHash;

        emit ThreatDetected(detectorName, patternHash, confidence, block.timestamp);
        return (true, confidence, patternHash);
    }
}
