from abc import ABC, abstractmethod

class MarketplacePlatform(ABC):
    """
    Abstract base class for all marketplace platform integrations.
    """

    @abstractmethod
    def create_listing(self, book: dict) -> str:
        """
        Creates a new listing for a book on the platform.

        Args:
            book: A dictionary containing book information.

        Returns:
            The ID of the newly created listing.
        """
        pass

    @abstractmethod
    def delete_listing(self, listing_id: str) -> None:
        """
        Deletes a listing from the platform.

        Args:
            listing_id: The ID of the listing to delete.
        """
        pass

    @abstractmethod
    def update_listing(self, listing_id: str, book: dict) -> None:
        """
        Updates an existing listing on the platform.

        Args:
            listing_id: The ID of the listing to update.
            book: A dictionary containing the updated book information.
        """
        pass

    @abstractmethod
    def get_listing(self, listing_id: str) -> dict:
        """
        Retrieves a listing from the platform.

        Args:
            listing_id: The ID of the listing to retrieve.

        Returns:
            A dictionary containing the listing information.
        """
        pass