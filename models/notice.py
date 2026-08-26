from pydantic import BaseModel, Field
from typing import List

class NoticeStructuredData(BaseModel):
    """
    Structured data extracted from a civic paperwork / government notice by DocumentAgent.
    Fields default to 'Not found' if missing or unstated.
    """
    notice_type: str = Field(default="Not found", description="Type of notice, e.g., 'Property Tax Delinquency Notice'")
    issuing_authority: str = Field(default="Not found", description="Government agency/authority issuing the notice")
    department: str = Field(default="Not found", description="Specific department within the agency")
    reference_number: str = Field(default="Not found", description="Case ID, Citation ID, Account #, or Reference number")
    citizen_name: str = Field(default="Not found", description="Addressee or property owner named on notice")
    property_id: str = Field(default="Not found", description="APN, parcel ID, vehicle VIN, or relevant asset identifier")
    amount: str = Field(default="Not found", description="Monetary sum owed, disputed, or referenced (with currency)")
    issue: str = Field(default="Not found", description="Core problem or reason the notice was sent")
    deadline: str = Field(default="Not found", description="Strict statutory due date or response deadline")
    required_action: str = Field(default="Not found", description="Immediate steps the recipient is required to take")
    mentioned_documents: List[str] = Field(default_factory=list, description="List of required supporting documents or proofs mentioned")
