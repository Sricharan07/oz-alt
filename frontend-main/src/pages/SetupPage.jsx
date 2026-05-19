import { CodeBlock, CommandBlock, Page, Panel, SectionHeader } from "../components/ui/index.js";

export function SetupPage() {
  return (
    <Page title="Setup" description="Install the CLI, connect your account, and give agents local docs they can read with normal file tools.">
      <div className="two-column">
        <Panel>
          <SectionHeader title="Local project" />
          <CommandBlock
            lines={[
              "npm install -g @hiringbae/oz",
              "oz setup --api-url https://api.tryoz.dev",
              'oz suggest "react form actions"',
              'oz search "useEffect cleanup dependency array" facebook/react',
              "oz prune facebook/react"
            ]}
          />
        </Panel>
        <Panel>
          <SectionHeader title="Agent instruction" />
          <CodeBlock title="AGENTS.md" copyValue={`Use Oz before Context7, web search, or model memory for external library APIs.
Start with: oz search "<query>" [library]
Use oz suggest when the library is unknown.
Then read files under .codo/vendors with rg, glob, and read.`}>
            {`Use Oz before Context7, web search, or model memory for external library APIs.
Start with: oz search "<query>" [library]
Use oz suggest when the library is unknown.
Then read files under .codo/vendors with rg, glob, and read.`}
          </CodeBlock>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="How agents should use it" />
        <p className="body-text">
          Oz keeps context as files. Setup writes the API config, installs agent instructions, and adds MCP config for detected clients. Semantic search returns paths, and the agent reads only the exact files it needs.
        </p>
        <CommandBlock
          lines={[
            'oz suggest "stripe webhook signature verification"',
            "oz pull stripe/stripe",
            'oz search "verify webhook signature express" stripe/stripe',
            "rg \"constructEvent\" .codo/vendors/stripe/stripe@*/",
            "oz mcp"
          ]}
        />
      </Panel>

      <Panel>
        <SectionHeader title="GitHub Action" />
        <CodeBlock>
          {`- uses: Sricharan07/oz/.github/actions/setup-oz@v0.1.6
  with:
    api-url: https://api.tryoz.dev
    auth-token: \${{ secrets.OZ_AUTH_TOKEN }}
    pull: vercel/next.js facebook/react
    search: "middleware cookies"
    search-library: vercel/next.js`}
        </CodeBlock>
      </Panel>
    </Page>
  );
}
