# Meta Ads MCP Server

A Meta (Facebook) Ads Management Control Protocol (MCP) server that enables seamless integration with Meta's advertising platform. This server provides tools for creating custom audiences and managing ad campaigns through the Meta Graph API.

## Features

- Create custom audiences from pre-hashed phone numbers
- Create and manage ad campaigns
- Configure ad sets with targeting options
- Create ads with customizable content
- Seamless integration with Meta's Graph API

## Prerequisites

- Python 3.7+
- uv package manager
- Meta Business Account
- Meta App with appropriate permissions
- Facebook Access Token with required permissions

## Installation

1. Install uv package manager if you haven't already:

```bash
pip install uv
```

2. Clone the repository:

```bash
git clone <repository-url>
cd mcp-meta-ads
```

3. Create and activate a virtual environment using uv:

```bash
uv venv
# On Windows
.venv\Scripts\activate
# On Unix/MacOS
source .venv/bin/activate
```

4. Install the required dependencies using uv:

```bash
uv pip install -r requirements.txt
```

## Configuration

1. Obtain a Facebook Access Token:

   - Go to [Meta for Developers](https://developers.facebook.com/)
   - Create or select your app
   - Generate a long-lived access token with the following permissions:
     - `ads_management`
     - `ads_read`
     - `read_audience_network_insights`

2. Add your access token in meta.py:
   - Add your Facebook access token:
   ```
   FB_ACCESS_TOKEN=your_access_token_here
   ```

## Usage

### Starting the MCP Server

Run the server using uv:

```bash
uv run --with mcp[cli] mcp run server/meta.py
```

### Available Tools

#### 1. Create Custom Audience

Creates a custom audience from pre-hashed phone numbers.

```python
await create_custom_audience(
    act_id="your_ad_account_id",
    hashed_content="path_to_hashed_phones.csv",
    audience_name="My Custom Audience",
    description="Optional description"
)
```

#### 2. Create Ad Campaign

Creates a complete ad campaign targeting a custom audience.

```python
await create_ad_campaign(
    act_id="your_ad_account_id",
    name="Campaign Name",
    objective="REACH",
    custom_audience_id="your_audience_id",
    daily_budget=50.0,
    page_id="your_page_id",
    ad_link="https://your-landing-page.com",
    ad_message="Your ad message",
    ad_title="Ad Title"
)
```

### Claude Desktop Configuration

1. Create a configuration file named `claude_config.json` in your Claude Desktop configuration directory:

```json
{
  "mcpServers": {
    "meta-ads-mcp-server": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        "D:\\pinelabs_meta_mcp\\mcp-meta-ads\\server\\meta.py"
      ]
    }
  }
}
```

2. Replace the following in the configuration:

   - `D:\\pinelabs_meta_mcp\\mcp-meta-ads\\server\\meta.py`: The absolute path to your MCP server installation
   - Note: Make sure to use double backslashes (`\\`) in Windows paths

3. Place the configuration file in one of these locations:

   - Windows: `%APPDATA%\Claude Desktop\config\`
   - macOS: `~/Library/Application Support/Claude Desktop/config/`
   - Linux: `~/.config/claude-desktop/config/`

4. Restart Claude Desktop to load the new configuration.

The MCP server will now be available in Claude Desktop. You can use the Meta Ads tools directly in your conversations with Claude.

## Error Handling

The server includes built-in error handling for API calls. All responses include error information if the operation fails. Check the response for an 'error' key to handle failures appropriately.

## Security Considerations

- Never commit your Facebook access token to version control
- Use environment variables or secure secret management for sensitive credentials
- Regularly rotate your access tokens
- Follow Meta's security best practices for ad account management

## Support

For issues and feature requests, please create an issue in the repository.
