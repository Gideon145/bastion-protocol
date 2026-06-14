// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title BaseDetector — Abstract base for composable threat detectors
/// @notice Every detector inherits this. Protocols compose only what they need.
abstract contract BaseDetector {
    uint8 public constant SEVERITY_LOW = 1;
    uint8 public constant SEVERITY_MEDIUM = 2;
    uint8 public constant SEVERITY_HIGH = 3;
    uint8 public constant SEVERITY_CRITICAL = 4;

    string public detectorName;
    uint8 public detectorSeverity;

    event ThreatDetected(
        string indexed detectorName,
        bytes32 indexed patternHash,
        uint256 confidence,
        uint256 timestamp
    );

    /// @notice Every detector implements this. Returns (isThreat, confidence 0-100, patternHash)
    function analyze(
        bytes calldata txData,
        bytes32[] calldata recentBlockHashes,
        uint256 blockNumber
    ) external virtual returns (bool, uint256, bytes32);

    /// @notice Optional: protocol queries if last block was a threat
    mapping(uint256 => bytes32) public threatAtBlock;
}
