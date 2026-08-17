from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WalletConnectRequest(BaseModel):
    user_id: str = Field(..., description="UUID of the student")
    wallet_address: str = Field(
        ..., description="Quai EVM wallet address (0x...)"
    )
    message: str = Field(
        ..., description="Signed cryptographic authentication challenge string"
    )
    signature: str = Field(
        ..., description="65-byte hex signature (0x...) from WalletConnect / Web3 provider"
    )


class WalletConnectResponse(BaseModel):
    user_id: str
    wallet_address: str
    verified: bool
    message: str


class WalletBalanceResponse(BaseModel):
    user_id: str
    wallet_address: str | None = None
    balance_quai: float
    balance_wei: str
    fiat_value_ngn: float
    network: str = "Quai Network Testnet"


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    wallet_address: str
    recipient_address: str
    amount: float
    tx_hash: str
    type: str
    status: str
    network: str
    block_number: int | None = None
    note: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletSendRequest(BaseModel):
    sender_id: str = Field(..., description="UUID of the sender student")
    recipient: str = Field(
        ..., description="Quai EVM address (0x...), email, or user UUID of the recipient"
    )
    amount_quai: float = Field(..., gt=0, description="Amount of QUAI to transfer")
    tx_hash: str | None = Field(
        None, description="Optional transaction hash if signed and broadcasted by client wallet"
    )
    note: str | None = Field(None, description="Optional transfer note or memo")


class WalletSendResponse(BaseModel):
    success: bool
    tx_hash: str
    amount_quai: float
    recipient: str
    status: str
    message: str


class WalletDashboardResponse(BaseModel):
    user_id: str
    wallet_address: str | None = None
    balance: WalletBalanceResponse
    transactions: list[TransactionResponse]
    qr_receive_address: str
    is_verified: bool
    trust_score: int
