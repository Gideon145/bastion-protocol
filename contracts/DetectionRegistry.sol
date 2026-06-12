// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title DetectionRegistry — On-chain attestation for exploit detections
/// @notice Every CRITICAL detection is hash-committed here for immutable proof
contract DetectionRegistry {
    struct DetectionRecord {
        uint256 id;
        bytes32 patternHash;
        uint8 severity;       // 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL
        uint256 confidence;   // 0-100
        bytes32 evidenceHash; // Blake3/SHA256 of detection evidence
        uint256 timestamp;
        address agent;
    }

    mapping(address => bool) public activeAgents;
    mapping(uint256 => DetectionRecord) public detections;
    uint256 public totalDetections;

    event DetectionRecorded(
        uint256 indexed id,
        bytes32 indexed patternHash,
        uint8 severity,
        uint256 confidence,
        address agent
    );

    modifier onlyAgent() {
        require(activeAgents[msg.sender], "Not an active agent");
        _;
    }

    function registerAgent(address agent) external {
        activeAgents[agent] = true;
    }

    function recordDetection(
        bytes32 patternHash,
        uint8 severity,
        uint256 confidence,
        bytes32 evidenceHash
    ) external onlyAgent returns (uint256) {
        uint256 id = ++totalDetections;
        detections[id] = DetectionRecord({
            id: id,
            patternHash: patternHash,
            severity: severity,
            confidence: confidence,
            evidenceHash: evidenceHash,
            timestamp: block.timestamp,
            agent: msg.sender
        });
        emit DetectionRecorded(id, patternHash, severity, confidence, msg.sender);
        return id;
    }
}
