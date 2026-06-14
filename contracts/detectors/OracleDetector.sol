// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./BaseDetector.sol";

/// @title OracleDetector — Detects oracle manipulation attacks
/// @notice Flags price deviations >10% from TWAP across liquidity pools.
///         Mango Markets lost $116M to this pattern in 2022.
contract OracleDetector is BaseDetector {
    uint256 public constant MAX_DEVIATION_BPS = 1000; // 10% = 1000 basis points
    uint256 public constant MIN_LIQUIDITY_USD = 500_000;

    constructor() {
        detectorName = "OracleDetector";
        detectorSeverity = SEVERITY_CRITICAL;
    }

    /// @param txData ABI-encoded: (reportedPrice uint256, twapPrice uint256, poolLiquidityUSD uint256, poolCount uint8)
    function analyze(
        bytes calldata txData,
        bytes32[] calldata /* recentBlockHashes */,
        uint256 blockNumber
    ) external override returns (bool isThreat, uint256 confidence, bytes32 patternHash) {
        (uint256 reportedPrice, uint256 twapPrice, uint256 liquidityUSD, uint8 poolCount) =
            abi.decode(txData, (uint256, uint256, uint256, uint8));

        if (twapPrice == 0 || liquidityUSD < MIN_LIQUIDITY_USD) return (false, 0, bytes32(0));

        // Calculate deviation in basis points
        uint256 deviation;
        if (reportedPrice > twapPrice) {
            deviation = ((reportedPrice - twapPrice) * 10000) / twapPrice;
        } else {
            deviation = ((twapPrice - reportedPrice) * 10000) / twapPrice;
        }

        if (deviation <= MAX_DEVIATION_BPS) return (false, 0, bytes32(0));

        // Confidence: deviation severity + affected pool count
        uint256 deviationScore = (deviation * 50) / MAX_DEVIATION_BPS; // 10% = 50, 20% = 100
        uint256 poolScore = uint256(poolCount) * 10;                     // 3 pools = 30, 5 pools = 50

        confidence = deviationScore + poolScore;
        if (confidence > 100) confidence = 100;

        patternHash = keccak256(abi.encodePacked("ORACLE_MANIP", deviation, poolCount, blockNumber));
        threatAtBlock[blockNumber] = patternHash;

        emit ThreatDetected(detectorName, patternHash, confidence, block.timestamp);
        return (true, confidence, patternHash);
    }
}
