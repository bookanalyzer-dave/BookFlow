from .base import MarketplacePlatform
from ebaysdk.trading import Connection as Trading

class EbayPlatform(MarketplacePlatform):
    """
    Concrete implementation for the eBay marketplace platform.
    """

    def __init__(self, app_id: str, dev_id: str, cert_id: str, token: str, config_file: str = None):
        self.api = Trading(
            appid=app_id,
            devid=dev_id,
            certid=cert_id,
            token=token,
            config_file=config_file, # Can be None
            siteid="77"  # Germany
        )

    def create_listing(self, book: dict) -> str:
        """
        Creates a new listing for a book on eBay using AddFixedPriceItem.
        """
        print(f"Creating eBay listing for book: {book.get('title')}")

        item = {
            "Item": {
                "Title": book.get("title"),
                "Description": book.get("description", "No description available."),
                "PrimaryCategory": {"CategoryID": "267"},  # Books
                "StartPrice": str(book.get("price", "9.99")),
                "CategoryMappingAllowed": "true",
                "Country": "DE",
                "Currency": "EUR",
                "ConditionID": "3000", # Used
                "DispatchTimeMax": "3",
                "ListingDuration": "GTC", # Good 'Til Canceled
                "ListingType": "FixedPriceItem",
                "PaymentMethods": "PayPal",
                "PayPalEmailAddress": "user@example.com", # Replace with actual PayPal email
                "PictureDetails": {"PictureURL": book.get("image_url")},
                "PostalCode": "10115", # Example postal code
                "Quantity": "1",
                "ReturnPolicy": {
                    "ReturnsAcceptedOption": "ReturnsAccepted",
                    "RefundOption": "MoneyBack",
                    "ReturnsWithinOption": "Days_14",
                    "ShippingCostPaidByOption": "Buyer",
                },
                "ShippingDetails": {
                    "ShippingType": "Flat",
                    "ShippingServiceOptions": {
                        "ShippingServicePriority": "1",
                        "ShippingService": "DE_DeutschePostBrief",
                        "ShippingServiceCost": "2.00",
                    },
                },
                "Site": "Germany",
            }
        }

        response = self.api.execute("AddFixedPriceItem", item)
        listing_id = response.reply.ItemID
        print(f"Successfully created eBay listing with ID: {listing_id}")
        return listing_id

    def delete_listing(self, listing_id: str) -> None:
        """
        Deletes a listing from eBay using EndFixedPriceItem.
        """
        print(f"Deleting eBay listing with ID: {listing_id}")
        request = {
            "ItemID": listing_id,
            "EndingReason": "NotAvailable" # Or another valid reason
        }
        self.api.execute("EndFixedPriceItem", request)
        print(f"Successfully deleted eBay listing with ID: {listing_id}")