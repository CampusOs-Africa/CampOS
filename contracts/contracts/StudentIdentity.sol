// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title StudentIdentity
 * @notice Quai Network Smart Contract for CampusOS Verified Student Identity.
 * @dev Stores ONLY SHA-256 cryptographic credential hashes and verified status flags.
 *      Never stores personally identifiable information (PII) on-chain.
 */
contract StudentIdentity {
    address public owner;

    // Mapping from user wallet address to SHA-256 credential hash (bytes32)
    mapping(address => bytes32) private _credentialHashes;

    // Mapping from user wallet address to verification status
    mapping(address => bool) private _verifiedStatus;

    // Events for indexing and audit trail
    event StudentRegistered(address indexed user, bytes32 indexed credHash, uint256 timestamp);
    event StudentVerified(address indexed user, uint256 timestamp);
    event StudentRevoked(address indexed user, uint256 timestamp);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "StudentIdentity: caller is not the owner");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    /**
     * @notice Register a student's SHA-256 credential hash and mark as verified.
     * @param user The wallet address of the student.
     * @param credHash The SHA-256 cryptographic hash of the verification record.
     */
    function registerStudent(address user, bytes32 credHash) external onlyOwner {
        require(user != address(0), "StudentIdentity: zero address invalid");
        require(credHash != bytes32(0), "StudentIdentity: empty credential hash invalid");

        _credentialHashes[user] = credHash;
        _verifiedStatus[user] = true;

        emit StudentRegistered(user, credHash, block.timestamp);
    }

    /**
     * @notice Re-verify an already registered student account.
     * @param user The wallet address of the student.
     */
    function verifyStudent(address user) external onlyOwner {
        require(user != address(0), "StudentIdentity: zero address invalid");
        require(_credentialHashes[user] != bytes32(0), "StudentIdentity: student not registered");

        _verifiedStatus[user] = true;

        emit StudentVerified(user, block.timestamp);
    }

    /**
     * @notice Revoke a student's verified status on-chain.
     * @param user The wallet address of the student.
     */
    function revokeStudent(address user) external onlyOwner {
        require(user != address(0), "StudentIdentity: zero address invalid");

        _verifiedStatus[user] = false;

        emit StudentRevoked(user, block.timestamp);
    }

    /**
     * @notice Check whether a student wallet address is currently verified.
     * @param user The wallet address of the student.
     * @return bool True if verified, false otherwise.
     */
    function isVerified(address user) external view returns (bool) {
        return _verifiedStatus[user];
    }

    /**
     * @notice Retrieve the SHA-256 credential hash stored on-chain for a student.
     * @param user The wallet address of the student.
     * @return bytes32 The SHA-256 credential hash.
     */
    function getCredentialHash(address user) external view returns (bytes32) {
        return _credentialHashes[user];
    }

    /**
     * @notice Transfer administrative ownership of the contract.
     * @param newOwner The address of the new owner.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "StudentIdentity: new owner is the zero address");
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}
