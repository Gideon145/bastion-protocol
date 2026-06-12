// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

/// @title ThreatSignatureRegistry — Write-once shared threat intel
/// @notice Stolen from ArbiGuard. One detection protects ALL pools on Robinhood.
///         Signatures are write-once, immutable, and read by every protected market.
contract ThreatSignatureRegistry {
    struct ThreatSignature {
        uint256 id;
        bytes32 featureHash;      // keccak256 of 8-element feature vector
        uint8 score;              // 0-100 deterministic score
        bytes32 evidenceHash;     // Blake3 of detection evidence
        uint256 timestamp;
        address reporter;         // Agent that published the threat
        bool active;              // Once tripped, stays active
    }

    mapping(bytes32 => bool) public publishedSignatures;  // featureHash → published
    mapping(uint256 => ThreatSignature) public signatures;
    uint256 public totalSignatures;

    // Protected pools can query: "has this threat signature been seen?"
    mapping(address => bool) public isProtectedPool;
    mapping(address => mapping(bytes32 => bool)) public poolBlocked;  // pool → featureHash → blocked

    event ThreatPublished(
        uint256 indexed id,
        bytes32 indexed featureHash,
        uint8 score,
        address indexed reporter
    );

    event PoolProtected(address indexed pool);
    event SignatureBlocked(address indexed pool, bytes32 indexed featureHash);

    modifier onlyAgent() {
        // In production: check ReputationRegistry for authorized agents
        _;
    }

    /// @notice Publish a threat signature — write-once, immutable
    function publishThreat(
        bytes32 featureHash,
        uint8 score,
        bytes32 evidenceHash
    ) external onlyAgent returns (uint256) {
        require(!publishedSignatures[featureHash], "Already published");

        uint256 id = ++totalSignatures;
        signatures[id] = ThreatSignature({
            id: id,
            featureHash: featureHash,
            score: score,
            evidenceHash: evidenceHash,
            timestamp: block.timestamp,
            reporter: msg.sender,
            active: true
        });
        publishedSignatures[featureHash] = true;

        emit ThreatPublished(id, featureHash, score, msg.sender);
        return id;
    }

    /// @notice Register a pool as protected by Bastion
    function protectPool(address pool) external {
        isProtectedPool[pool] = true;
        emit PoolProtected(pool);
    }

    /// @notice Block a specific threat signature for a specific pool
    function blockSignature(address pool, bytes32 featureHash) external {
        require(isProtectedPool[pool], "Pool not protected");
        require(publishedSignatures[featureHash], "Signature not published");
        poolBlocked[pool][featureHash] = true;
        emit SignatureBlocked(pool, featureHash);
    }

    /// @notice Check if a transaction should be blocked (signature exists + pool is protected)
    function shouldBlock(address pool, bytes32 featureHash) external view returns (bool) {
        return isProtectedPool[pool] && publishedSignatures[featureHash];
    }
}
