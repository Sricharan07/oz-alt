# create_agent

**Kind:** function
**Signature:** `def call(self):`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/atoms/atoms_client.py#call

## Example

```python
def call(self):
        """Call management and analytics."""
        return self._call

    @property
    def audience(self):
        """Audience management."""
        return self._audience

    @property
    def campaign(self):
        """Campaign management."""
        return self._campaign

    @property
    def kb(self):
        """Knowledge Base management."""
        return self._kb

    # Agent Methods
    @validate_call
    def create_agent(
        self,
        create_agent_request: CreateAgentRequest,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ):
        return self.agents_api.agent_post(
            create_agent_request=create_agent_request,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

    def delete_agent(
        self,
        id: str,
        **kwargs
    ):
        """
        Delete (archive) an agent by ID.

        Note: Backend uses /agent/{id}/archive endpoint.
        """
        import requests
        url = f"{self._get_base_url()}/agent/{id}/archive"
        headers = self._get_auth_headers()

        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_agent_by_id(
        self,
        id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get agent by ID with full details.

        Returns:
            Dict with agent details including globalKnowledgeBaseId
        """
        import requests
        url = f"{self._get_base_url()}/agent/{id}"
        headers = self._get_auth_headers()

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    @validate_call
    def get_agents(
        self,
        page: Optional[StrictInt] = None,
        offset: Optional[StrictInt] = None,
        search: Optional[StrictStr] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ):
        return self.agents_api.agent_get(
            page=page,
            offset=offset,
            search=search,
            _request_timeout=_request_timeout,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

    @validate_call
    def update_agent(
        self,
        id: StrictStr,
        agent_id_patch_request: AgentIdPatchRequest,
        _request_timeout: Union[
            None,
```
