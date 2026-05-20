# disconnect

**Kind:** function
**Signature:** `class SessionHandler:`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/atoms/agent/server.py#sessionhandler

## Example

```python
class SessionHandler:
    """Manages all active WebSocket sessions"""

    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}

    async def create_session(
        self,
        websocket: WebSocket,
        setup_handler: Callable[[AgentSession], Awaitable[None]],
    ) -> str:
        """
        Create and start a new session.

        Args:
            websocket: WebSocket connection
            session_id: Unique session ID
            setup_handler: Async function to setup the session graph
        """
        # Create session
        session_id = f"session-{uuid.uuid4()}"
        session = AgentSession(
            websocket=websocket, session_id=session_id, setup_handler=setup_handler
        )
        await session.initialize()

        self._sessions[session_id] = session

        return session_id

    def disconnect(self, session_id: str) -> None:
        """Remove a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.debug(f"Removed session {session_id}")

    @property
    def active_sessions(self) -> int:
        """Get number of active sessions"""
        return len(self._sessions)

    async def shutdown(self) -> None:
        """Shutdown all sessions"""
        if self._sessions:
            logger.info(f"Closing {len(self._sessions)} active sessions")
            await asyncio.gather(
                *[session.cleanup() for session in self._sessions.values()],
                return_exceptions=True,
            )

            self._sessions.clear()
```
