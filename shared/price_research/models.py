from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field

class MarketStrategy(str, Enum):
    AGGRESSIVE = "aggressive"       # Unterbieten um jeden Preis (Liquidität vor Marge)
    BALANCED = "balanced"           # Marktüblicher Preis (guter Kompromiss)
    PATIENT = "patient"             # Hoher Preis, warten auf den richtigen Käufer (Long-Tail)
    LIQUIDATION = "liquidation"     # Weg damit, egal wie billig

class Condition(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    VERY_GOOD = "very_good"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"

class CompetitorOffer(BaseModel):
    """Repräsentiert ein bereinigtes Angebot der Konkurrenz."""
    seller_name: str = Field(description="Name des Verkäufers")
    price: float = Field(description="Preis in EUR")
    condition: str = Field(description="Zustand laut Angebot (normiert)")
    platform: str = Field(description="Plattform (Amazon, eBay, etc.)")
    is_prime: bool = Field(default=False, description="Ist es ein Prime/FBA Angebot?")
    
class PriceRange(BaseModel):
    min_price: float
    max_price: float
    avg_price: float

class MarketAnalysis(BaseModel):
    """Das Ergebnis der KI-gestützten Marktanalyse."""
    
    # Die Empfehlung
    recommended_price: float = Field(description="Der optimale Verkaufspreis")
    min_price_limit: float = Field(description="Untergrenze (Floor Price) - nicht unterschreiten")
    strategy_used: MarketStrategy = Field(description="Die angewandte Strategie")
    confidence: float = Field(description="Vertrauen in die Analyse (0.0 - 1.0)")
    
    # Marktdaten (Zusammenfassung)
    competitor_count: int = Field(description="Anzahl analysierter Konkurrenten")
    market_price_range: PriceRange = Field(description="Preisspanne am Markt")
    
    # Erklärung
    reasoning: str = Field(description="Warum dieser Preis? (Kurzfassung für UI)")
    internal_notes: Optional[str] = Field(description="Technische Details zur Entscheidung")
