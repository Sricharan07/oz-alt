import { CodeBlock, CommandBlock, Page, Panel, SectionHeader } from "../components/ui/index.js";

export function SetupPage() {
  return (
    <Page title="Setup" description="Install the CLI, authenticate once, and let agents use local docs as files.">
      <div className="two-column">
        <Panel>
          <SectionHeader title="CLI workflow" />
          <CommandBlock
            lines={[
              "npm install -g @hiringbae/oz",
              "oz login --api-url https://api.tryoz.dev",
              "oz init",
              'oz suggest "react form actions"',
              "oz pull facebook/react",
              'oz search "useEffect cleanup dependency array" facebook/react',
              "oz prune facebook/react"
            ]}
          />
        </Panel>
        <Panel>
          <SectionHeader title="Agent instruction" />
          <CodeBlock>
            {`Use Oz before guessing external library APIs.
Start with: oz search "<query>" [library]
Then read files under .codo/vendors with rg, glob, and read.`}
          </CodeBlock>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="Path-first MCP" />
        <p className="body-text">
          Oz exposes a small MCP wrapper for clients that prefer native tools. The default tool returns paths and line ranges, not large snippet blobs.
        </p>
        <CodeBlock>
          {`{
  "mcpServers": {
    "oz": {
      "command": "oz",
      "args": ["mcp"],
      "env": {
        "OZ_API_URL": "https://api.tryoz.dev"
      }
    }
  }
}`}
        </CodeBlock>
      </Panel>

      <Panel>
        <SectionHeader title="GitHub Action" />
        <CodeBlock>
          {`- uses: Sricharan07/oz/.github/actions/setup-oz@v0.1.5
  with:
    api-url: https://api.tryoz.dev
    pull: vercel/next.js facebook/react
  env:
    OZ_AUTH_TOKEN: \${{ secrets.OZ_AUTH_TOKEN }}`}
        </CodeBlock>
      </Panel>
    </Page>
  );
}
