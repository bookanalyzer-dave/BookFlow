from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Book:
    """
    Represents the structure of a book document in Firestore, aligned with the
    implemented architecture.
    """
    userId: str
    status: str
    title: str = ""
    author: str = ""
    isbn: str = ""
    identifiedVia: str = ""
    condition: str = ""
    imageUrls: List[str] = field(default_factory=list)
    generatedDescription: str = ""
    calculatedPrice: float = 0.0
    floorPrice: float = 0.0
    errorDetails: str = ""
    createdAt: Any = None  # Firestore Timestamp
    soldAt: Any = None      # Firestore Timestamp
    soldOnPlatform: str = ""
    soldPrice: float = 0.0
    listings: Dict[str, Any] = field(default_factory=dict)
    bookId: str = "" # Firestore document ID

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        """Creates a Book instance from a dictionary."""
        # Get valid fields from the dataclass
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Book instance to a dictionary."""
        import dataclasses
        return dataclasses.asdict(self)
