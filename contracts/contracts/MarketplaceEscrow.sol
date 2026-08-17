// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IStudentIdentity {
    function isVerified(address user) external view returns (bool);
}

/**
 * @title MarketplaceEscrow
 * @notice Quai Network Smart Contract Escrow for CampusOS Marketplace.
 * @dev Protects campus P2P transactions by locking buyer funds until delivery is confirmed.
 *      Enforces that only verified students (on StudentIdentity.sol) can act as sellers.
 *      Uses Checks-Effects-Interactions (CEI) pattern and OpenZeppelin ReentrancyGuard.
 */
contract MarketplaceEscrow is Ownable, ReentrancyGuard {
    enum EscrowState {
        NON_EXISTENT,
        CREATED,
        FUNDED,
        DELIVERED,
        COMPLETED,
        REFUNDED,
        CANCELLED,
        DISPUTED
    }

    struct Escrow {
        address buyer;         // 20 bytes ──┐ slot 0 (24 bytes)
        uint32 createdAt;      // 4 bytes  ──┘
        address seller;        // 20 bytes ──┐ slot 1 (24 bytes)
        uint32 expiresAt;      // 4 bytes  ──┘
        uint256 amount;        // 32 bytes ─── slot 2
        EscrowState state;     // 1 byte   ─── slot 3
    }

    IStudentIdentity public studentIdentity;
    uint32 public defaultTimeoutDuration = 14 days;

    // Mapping from unique order ID (bytes32) to Escrow struct
    mapping(bytes32 => Escrow) public escrows;

    // Events
    event EscrowCreated(
        bytes32 indexed orderId,
        address indexed buyer,
        address indexed seller,
        uint256 amount
    );
    event EscrowDelivered(bytes32 indexed orderId);
    event EscrowFunded(
        bytes32 indexed orderId,
        uint256 amount,
        uint256 expiresAt
    );
    event EscrowReleased(
        bytes32 indexed orderId,
        address indexed seller,
        uint256 amount
    );
    event EscrowRefunded(
        bytes32 indexed orderId,
        address indexed buyer,
        uint256 amount
    );
    event EscrowCancelled(bytes32 indexed orderId);
    event EscrowDisputed(
        bytes32 indexed orderId,
        address indexed disputer
    );
    event DisputeResolved(
        bytes32 indexed orderId,
        bool favorSeller,
        uint256 amount
    );
    event StudentIdentityContractUpdated(
        address indexed oldContract,
        address indexed newContract
    );
    event TimeoutDurationUpdated(
        uint32 oldDuration,
        uint32 newDuration
    );

    // Modifiers
    modifier inState(bytes32 orderId, EscrowState expectedState) {
        require(
            escrows[orderId].state == expectedState,
            "MarketplaceEscrow: invalid escrow state"
        );
        _;
    }

    modifier onlyBuyer(bytes32 orderId) {
        require(
            msg.sender == escrows[orderId].buyer,
            "MarketplaceEscrow: caller is not the buyer"
        );
        _;
    }

    modifier onlySeller(bytes32 orderId) {
        require(
            msg.sender == escrows[orderId].seller,
            "MarketplaceEscrow: caller is not the seller"
        );
        _;
    }

    modifier onlyBuyerOrSeller(bytes32 orderId) {
        require(
            msg.sender == escrows[orderId].buyer || msg.sender == escrows[orderId].seller,
            "MarketplaceEscrow: caller is not an order participant"
        );
        _;
    }

    /**
     * @notice Constructor initializes the contract owner and links StudentIdentity.sol.
     * @param studentIdentityAddress Address of the deployed StudentIdentity contract.
     */
    constructor(address studentIdentityAddress) Ownable(msg.sender) {
        require(
            studentIdentityAddress != address(0),
            "MarketplaceEscrow: zero address for StudentIdentity"
        );
        studentIdentity = IStudentIdentity(studentIdentityAddress);
    }

    /**
     * @notice Create a new marketplace escrow for an order.
     * @param orderId Unique bytes32 identifier of the order.
     * @param buyer Wallet address of the buyer.
     * @param seller Wallet address of the seller (must be verified on StudentIdentity).
     * @param amount Required deposit amount in wei.
     */
    function createEscrow(
        bytes32 orderId,
        address buyer,
        address seller,
        uint256 amount
    ) external onlyOwner {
        require(orderId != bytes32(0), "MarketplaceEscrow: invalid order ID");
        require(buyer != address(0) && seller != address(0), "MarketplaceEscrow: zero address invalid");
        require(buyer != seller, "MarketplaceEscrow: buyer and seller cannot be identical");
        require(amount > 0, "MarketplaceEscrow: amount must be greater than zero");
        require(
            escrows[orderId].state == EscrowState.NON_EXISTENT,
            "MarketplaceEscrow: escrow already exists"
        );
        require(
            studentIdentity.isVerified(seller),
            "MarketplaceEscrow: seller must be a verified student"
        );

        escrows[orderId] = Escrow({
            buyer: buyer,
            createdAt: uint32(block.timestamp),
            seller: seller,
            expiresAt: 0,
            amount: amount,
            state: EscrowState.CREATED
        });

        emit EscrowCreated(orderId, buyer, seller, amount);
    }

    /**
     * @notice Deposit funds into a created escrow.
     * @param orderId Unique bytes32 identifier of the order.
     */
    function deposit(bytes32 orderId)
        external
        payable
        inState(orderId, EscrowState.CREATED)
        nonReentrant
    {
        Escrow storage escrow = escrows[orderId];
        require(
            msg.value == escrow.amount,
            "MarketplaceEscrow: incorrect deposit amount"
        );
        require(
            msg.sender == escrow.buyer || msg.sender == owner(),
            "MarketplaceEscrow: only buyer or admin can deposit"
        );

        escrow.expiresAt = uint32(block.timestamp) + defaultTimeoutDuration;
        escrow.state = EscrowState.FUNDED;

        emit EscrowFunded(orderId, msg.value, escrow.expiresAt);
    }

    /**
     * @notice Buyer confirms the item has been delivered.
     * @param orderId Unique bytes32 identifier of the order.
     */
    function confirmDelivery(bytes32 orderId)
        external
        inState(orderId, EscrowState.FUNDED)
        onlyBuyer(orderId)
    {
        escrows[orderId].state = EscrowState.DELIVERED;
        emit EscrowDelivered(orderId);
    }

    /**
     * @notice Release escrowed funds to the seller after delivery confirmation.
     * @param orderId Unique bytes32 identifier of the order.
     */
    function release(bytes32 orderId)
        external
        nonReentrant
    {
        Escrow storage escrow = escrows[orderId];
        require(
            escrow.state == EscrowState.FUNDED || escrow.state == EscrowState.DELIVERED,
            "MarketplaceEscrow: escrow not in releasable state"
        );
        require(
            msg.sender == escrow.buyer || msg.sender == owner(),
            "MarketplaceEscrow: only buyer or admin can release escrow"
        );

        address seller = escrow.seller;
        uint256 amount = escrow.amount;

        // CEI Pattern: Update state BEFORE external call
        escrow.state = EscrowState.COMPLETED;

        (bool success, ) = seller.call{value: amount}("");
        require(success, "MarketplaceEscrow: Quai transfer to seller failed");

        emit EscrowReleased(orderId, seller, amount);
    }

    /**
     * @notice Refund escrowed funds to the buyer (by seller or admin).
     * @param orderId Unique bytes32 identifier of the order.
     */
    function refund(bytes32 orderId)
        external
        inState(orderId, EscrowState.FUNDED)
        nonReentrant
    {
        Escrow storage escrow = escrows[orderId];
        require(
            msg.sender == escrow.seller || msg.sender == owner(),
            "MarketplaceEscrow: only seller or admin can refund escrow"
        );

        address buyer = escrow.buyer;
        uint256 amount = escrow.amount;

        // CEI Pattern: Update state BEFORE external call
        escrow.state = EscrowState.REFUNDED;

        (bool success, ) = buyer.call{value: amount}("");
        require(success, "MarketplaceEscrow: Quai transfer to buyer failed");

        emit EscrowRefunded(orderId, buyer, amount);
    }

    /**
     * @notice Cancel an unfunded escrow.
     * @param orderId Unique bytes32 identifier of the order.
     */
    function cancel(bytes32 orderId)
        external
        inState(orderId, EscrowState.CREATED)
    {
        Escrow storage escrow = escrows[orderId];
        require(
            msg.sender == escrow.buyer ||
            msg.sender == escrow.seller ||
            msg.sender == owner(),
            "MarketplaceEscrow: unauthorized cancellation"
        );

        escrow.state = EscrowState.CANCELLED;
        emit EscrowCancelled(orderId);
    }

    /**
     * @notice Dispute a funded escrow, freezing funds until admin resolution.
     * @param orderId Unique bytes32 identifier of the order.
     */
    function dispute(bytes32 orderId)
        external
        inState(orderId, EscrowState.FUNDED)
        onlyBuyerOrSeller(orderId)
    {
        escrows[orderId].state = EscrowState.DISPUTED;
        emit EscrowDisputed(orderId, msg.sender);
    }

    /**
     * @notice Administrative resolution of a disputed escrow.
     * @param orderId Unique bytes32 identifier of the order.
     * @param favorSeller True to release to seller, false to refund buyer.
     */
    function resolveDispute(bytes32 orderId, bool favorSeller)
        external
        onlyOwner
        inState(orderId, EscrowState.DISPUTED)
        nonReentrant
    {
        Escrow storage escrow = escrows[orderId];
        uint256 amount = escrow.amount;

        if (favorSeller) {
            address seller = escrow.seller;
            escrow.state = EscrowState.COMPLETED;
            (bool success, ) = seller.call{value: amount}("");
            require(success, "MarketplaceEscrow: dispute Quai transfer to seller failed");
            emit EscrowReleased(orderId, seller, amount);
        } else {
            address buyer = escrow.buyer;
            escrow.state = EscrowState.REFUNDED;
            (bool success, ) = buyer.call{value: amount}("");
            require(success, "MarketplaceEscrow: dispute Quai transfer to buyer failed");
            emit EscrowRefunded(orderId, buyer, amount);
        }

        emit DisputeResolved(orderId, favorSeller, amount);
    }

    /**
     * @notice Claim a refund after the escrow timeout duration has expired without delivery.
     * @param orderId Unique bytes32 identifier of the order.
     */
    function refundAfterTimeout(bytes32 orderId)
        external
        inState(orderId, EscrowState.FUNDED)
        onlyBuyer(orderId)
        nonReentrant
    {
        Escrow storage escrow = escrows[orderId];
        require(
            block.timestamp > escrow.expiresAt,
            "MarketplaceEscrow: escrow has not timed out yet"
        );

        address buyer = escrow.buyer;
        uint256 amount = escrow.amount;

        escrow.state = EscrowState.REFUNDED;

        (bool success, ) = buyer.call{value: amount}("");
        require(success, "MarketplaceEscrow: timeout refund Quai transfer failed");

        emit EscrowRefunded(orderId, buyer, amount);
    }

    /**
     * @notice Update the linked StudentIdentity contract address.
     * @param newStudentIdentity Address of the new StudentIdentity contract.
     */
    function setStudentIdentity(address newStudentIdentity) external onlyOwner {
        require(
            newStudentIdentity != address(0),
            "MarketplaceEscrow: zero address invalid"
        );
        address old = address(studentIdentity);
        studentIdentity = IStudentIdentity(newStudentIdentity);
        emit StudentIdentityContractUpdated(old, newStudentIdentity);
    }

    /**
     * @notice Update the default timeout duration for new escrows.
     * @param newDurationSeconds Duration in seconds.
     */
    function setTimeoutDuration(uint32 newDurationSeconds) external onlyOwner {
        require(
            newDurationSeconds >= 1 hours && newDurationSeconds <= 365 days,
            "MarketplaceEscrow: timeout duration out of bounds"
        );
        uint32 old = defaultTimeoutDuration;
        defaultTimeoutDuration = newDurationSeconds;
        emit TimeoutDurationUpdated(old, newDurationSeconds);
    }

    /**
     * @notice Get full escrow details for an order.
     */
    function getEscrow(bytes32 orderId)
        external
        view
        returns (
            address buyer,
            address seller,
            uint256 amount,
            uint32 createdAt,
            uint32 expiresAt,
            EscrowState state
        )
    {
        Escrow memory esc = escrows[orderId];
        return (
            esc.buyer,
            esc.seller,
            esc.amount,
            esc.createdAt,
            esc.expiresAt,
            esc.state
        );
    }
}
