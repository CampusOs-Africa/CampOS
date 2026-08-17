// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../contracts/StudentIdentity.sol";

/**
 * @title StudentIdentityTest
 * @notice Foundry unit test suite for CampusOS StudentIdentity contract on Quai Network.
 */
contract StudentIdentityTest {
    StudentIdentity public identityContract;
    address public owner = address(this);
    address public student = address(0x1234567890123456789012345678901234567890);
    address public unauthorized = address(0x0987654321098765432109876543210987654321);

    bytes32 public sampleHash = keccak256(abi.encodePacked("user-101|amina.bello@unijos.edu.ng"));

    event StudentRegistered(address indexed user, bytes32 indexed credHash, uint256 timestamp);
    event StudentVerified(address indexed user, uint256 timestamp);
    event StudentRevoked(address indexed user, uint256 timestamp);

    function setUp() public {
        identityContract = new StudentIdentity();
    }

    function test_InitialState() public view {
        require(identityContract.owner() == owner, "Owner mismatch");
        require(!identityContract.isVerified(student), "Should be unverified initially");
        require(identityContract.getCredentialHash(student) == bytes32(0), "Hash should be zero initially");
    }

    function test_RegisterStudent() public {
        identityContract.registerStudent(student, sampleHash);
        require(identityContract.isVerified(student), "Student should be verified");
        require(identityContract.getCredentialHash(student) == sampleHash, "Credential hash mismatch");
    }

    function test_VerifyStudent() public {
        identityContract.registerStudent(student, sampleHash);
        identityContract.verifyStudent(student);
        require(identityContract.isVerified(student), "Student should remain verified");
    }

    function test_RevokeStudent() public {
        identityContract.registerStudent(student, sampleHash);
        identityContract.revokeStudent(student);
        require(!identityContract.isVerified(student), "Student should be revoked");
        // Hash should remain on-chain for auditability
        require(identityContract.getCredentialHash(student) == sampleHash, "Hash should be preserved after revocation");
    }
}
