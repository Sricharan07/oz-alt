# KB

```python
class KB:
    """
    Manager for Knowledge Base operations.

    Can be used standalone:
        kb = KB()
        kb.create(...)

    Or via AtomsClient:
        client = AtomsClient()
        client.kb.create(...)
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None
    ):
        """
        Initialize KB manager.

        Args:
            base_url: API base URL (default: atoms.smallest.ai)
            api_key: API key (default: SMALLEST_API_KEY env var)
        """
        self.base_url = base_url or os.environ.get("SMALLEST_BASE_URL", DEFAULT_BASE_URL)
        self.api_key = api_key or os.environ.get("SMALLEST_API_KEY", "")

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create(
        self,
        name: str = None,
        description: str = None,
        file_paths: List[str] = None,
        urls: List[str] = None,
        text: str = None
    ) -> Dict[str, Any]:
        """
        Create a new Knowledge Base.

        Args:
            name: KB name
            description: KB description
            file_paths: List of PDF file paths to upload
            urls: List of URLs to scrape
            text: Text content (may not be available via API yet)

        Returns:
            Created KB data
        """
        # Step 1: Create KB Container
        url = f"{self.base_url}/knowledgebase"
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"

        payload = {}
        if name: payload["name"] = name
        if description: payload["description"] = description

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        kb_data = response.json()

        # Handle response format: {"status": true, "data": "kb_id_string"}
        kb_id = kb_data.get("data")
        if isinstance(kb_id, dict):
            kb_id = kb_id.get("_id")

        # Step 2: Upload PDF Files
        if file_paths:
            for file_path in file_paths:
                self.add_file(kb_id, file_path)

        # Step 3: Scrape URLs
        if urls:
            self.scrape_urls(kb_id, urls)

        # Step 4: Add text (may not be available yet)
        if text:
            self.add_text(kb_id, text)

        # Return consistent format
        return {"status": True, "data": {"_id": kb_id}}

    def get(self, kb_id: str) -> Dict[str, Any]:
        """Get knowledge base details."""
        url = f"{self.base_url}/knowledgebase/{kb_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def list(self) -> Dict[str, Any]:
        """List all knowledge bases."""
        url = f"{self.base_url}/knowledgebase"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def delete(self, kb_id: str) -> Dict[str, Any]:
        """Delete a knowledge base."""
        url = f"{self.base_url}/knowledgebase/{kb_id}"
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def get_items(self, kb_id: str) -> Dict[str, Any]:
        """Get all items in a knowledge base."""
        url = f"{self.base_url}/knowledgebase/{kb_id}/items"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def delete_item(self, kb_id: str, item_id: str) -> Dict[str, Any]:
        """Delete an item from a knowledge base."""
```
