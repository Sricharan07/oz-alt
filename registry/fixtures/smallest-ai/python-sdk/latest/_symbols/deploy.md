# deploy

**Kind:** function
**Signature:** `def init():`
**Source:** https://raw.githubusercontent.com/smallest-inc/smallest-python-sdk/main/smallestai/cli/agent.py#init

## Example

```python
def init():
        """Initialize the agent configuration in the current directory."""
        asyncio.run(async_init())

    async def async_init():
        """Async implementation of init command."""
        agent_id = project_config.get_agent_id()

        if agent_id:
            console.print(
                f"[green]Agent already initialized with ID: [bold]{agent_id}[/bold][/green]"
            )
            return

        # Check if user is logged in
        credentials = auth_client.get_credentials()
        if not credentials or not credentials.get("access_token"):
            console.print(
                "[red]Error: You must be logged in first. Run 'smallestai auth login'[/red]"
            )
            raise typer.Exit(1)

        access_token = credentials["access_token"]

        console.print("[dim]Fetching agents...[/dim]")
        try:
            agent_data = await atoms_client.get_agents(access_token)
        except Exception as e:
            console.print(f"[red]Error fetching agents: {e}[/red]")
            return

        if not agent_data.agents:
            console.print(
                "[yellow]No agents found. Create an agent first at https://console.smallest.ai[/yellow]"
            )
            return

        choices = [
            questionary.Choice(
                title=f"{agent.name} - ID: {agent.id}",
                value=agent.id,
            )
            for agent in agent_data.agents
        ]

        selected_agent = await questionary.select(
            message="Select an agent to link",
            choices=choices,
            pointer="> ",
        ).ask_async()

        if not selected_agent:
            console.print("[red]No agent selected[/red]")
            return

        project_config.set_agent_id(selected_agent)
        console.print("[green]Agent initialized successfully![/green]")

    @app.command()
    def deploy(
        entry_point: str = typer.Option(
            "server.py",
            "--entry-point",
            "-e",
            help="Entry point file name (e.g., server.py)",
        ),
    ):
        """
        Deploy an agent to the Atoms platform.

        Packages the agent code directory into a zip file and deploys it to the backend.
        """
        asyncio.run(async_deploy(".", entry_point))

    async def async_deploy(directory: str, entry_point: str):
        """Deploy an agent asynchronously."""
        agent_id = project_config.get_agent_id()

        if not agent_id:
            console.print(
                "[red]Agent not initialized. Run 'smallestai agent init' first.[/red]"
            )
            return

        # Check if user is logged in
        credentials = auth_client.get_credentials()
        if not credentials or not credentials.get("access_token"):
            console.print(
                "[red]Error: You must be logged in first. Run 'smallestai auth login'[/red]"
            )
            raise typer.Exit(1)

        access_token = credentials["access_token"]

        dir_path = Path(directory)
        if not dir_path.exists():
            console.print(f"[red]Error: Directory '{directory}' does not exist.[/red]")
            return

        if not dir_path.is_dir():
            console.print(f"[red]Error: '{directory}' is not a directory.[/red]")
            return

        # Check if entry point file exists
        entry_point_path = dir_path / entry_point
        if not entry_point_path.exists():
            console.print(
                f"[red]Error: Entry point file '{entry_point}' not found in '{directory}'.[/red]"
            )
            return

        console.print(
            f"[bold cyan]Deploying agent from: {dir_path.absolute()}[/bold cyan]"
        )
        console.print(f"[dim]Entry point: {entry_point}[/dim]")
        console.print(f"[dim]Agent ID: {agent_id}[/dim]\n")

        # Create zip file in memory
        console.print("[yellow]Packaging agent code...[/yellow]")
        zip_buffer: BytesIO = create_zip_from_directory(dir_path)
```
