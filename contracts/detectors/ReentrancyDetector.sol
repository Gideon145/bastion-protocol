// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import "./BaseDetector.sol";

/// @title ReentrancyDetector — Detects reentrancy attack patterns
/// @notice Flags recursive call depth >3 with state-modifying operations.
///         Cream Finance lost $130M to this pattern in 2021.
contract ReentrancyDetector is BaseDetector {
    uint256 public constant MIN_CALL_DEPTH = 3;
    uint256 public constant MAX_CALL_DEPTH = 10;

    constructor() {
        detectorName = "ReentrancyDetector";
        detectorSeverity = SEVERITY_HIGH;
    }

    /// @param txData ABI-encoded: (callDepth uint8, hasStateChange bool, valueTransferred uint256, contractAge uint256)
    function analyze(
        bytes calldata txData,
        bytes32[] calldata /* recentBlockHashes */,
        uint256 blockNumber
    ) external override returns (bool isThreat, uint256 confidence, bytes32 patternHash) {
        (uint8 callDepth, bool hasStateChange, uint256 valueTransferred, uint256 contractAge) =
            abi.decode(txData, (uint8, bool, uint256, uint256));

        if (callDepth < MIN_CALL_DEPTH || !hasStateChange) return (false, 0, bytes32(0));

        // Confidence: call depth + value at risk + contract age (newer = riskier)
        uint256 depthScore = uint256(callDepth) * 20;               // 3 = 60, 6 = 120
        uint256 valueScore = (valueTransferred * 20) / 1 ether;     // 1 ETH = 20, 5 ETH = 100
        uint256 ageScore = contractAge < 7 days ? 30 : (contractAge < 30 days ? 15 : 0);

        confidence = depthScore + valueScore + ageScore;
        if (confidence > 100) confidence = 100;

        patternHash = keccak256(abi.encodePacked("REENTRANCY", callDepth, valueTransferred, blockNumber));
        threatAtBlock[blockNumber] = patternHash;

        emit ThreatDetected(detectorName, patternHash, confidence, block.timestamp);
        return (true, confidence, patternHash);
    }
}
