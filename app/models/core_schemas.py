from pydantic import BaseModel

# Quando o Core avisa de um leilão
class RideAuctionNotification(BaseModel):
    rideUuid: str
    origin: dict
    destination: dict
    originServiceId: str
    passengerId: str
    passengerName: str
    logicalTimestamp: int
    auctionDeadline: str

# Quando você responde a um leilão
class ProposalResponse(BaseModel):
    estimatedEta: int
    estimatedPrice: float
    logicalTimestamp: int

# Quando o Core te dá a vitória
class RideAssignment(BaseModel):
    rideUuid: str
    origin: dict
    destination: dict
    passengerId: str
    passengerName: str
    originServiceId: str
    logicalTimestamp: int
    lockExpiresAt: str