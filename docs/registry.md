# MCP Registry

The repository includes [server.json](../server.json) for the official MCP
Registry.

Current namespace:

```text
io.github.mscott9160-web/achlens
```

Before publishing:

1. Make the GitHub repository public. The official Registry does not support
   private servers.
2. Publish the matching `achlens` version to PyPI through the trusted-publishing
   release workflow.
3. Install the official `mcp-publisher` CLI.
4. Run `mcp-publisher validate` locally.
5. Authenticate with `mcp-publisher login github`.
6. Publish with `mcp-publisher publish`.

Do not publish until the package version, README ownership marker, PyPI package,
and `server.json` version all match.