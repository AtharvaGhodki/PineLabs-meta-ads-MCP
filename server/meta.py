from mcp.server.fastmcp import FastMCP
import httpx
import json
import sys
from typing import Dict, List, Optional, Any

# --- Constants ---
FB_API_VERSION = "v22.0"
FB_GRAPH_URL = f"https://graph.facebook.com/{FB_API_VERSION}"

# Create an MCP server
mcp = FastMCP("meta-ads-mcp-server")

# Add a global variable to store the token
FB_ACCESS_TOKEN = "your_access_token_here"

def _get_fb_access_token() -> str:
    """
    Get Facebook access token from command line arguments.
    Caches the token in memory after first read.

    Returns:
        str: The Facebook access token.

    Raises:
        Exception: If no token is provided in command line arguments.
    """
    global FB_ACCESS_TOKEN
    if FB_ACCESS_TOKEN is None:
        # Look for --fb-token argument
        if "--fb-token" in sys.argv:
            token_index = sys.argv.index("--fb-token") + 1
            if token_index < len(sys.argv):
                FB_ACCESS_TOKEN = sys.argv[token_index]
                print(f"Using Facebook token from command line arguments")
            else:
                raise Exception("--fb-token argument provided but no token value followed it")
        else:
            raise Exception("Facebook token must be provided via '--fb-token' command line argument")

    return FB_ACCESS_TOKEN

async def _make_graph_api_call(url: str, params: Dict[str, Any], method: str = 'GET', data: Optional[Dict] = None) -> Dict:
    """Makes an async request to the Facebook Graph API and handles the response."""
    async with httpx.AsyncClient() as client:
        try:
            if method == 'GET':
                response = await client.get(url, params=params, timeout=30.0)
            elif method == 'POST':
                response = await client.post(url, params=params, json=data, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making Graph API call to {url}: {e}")
            return None

# --- MCP Tools ---

@mcp.tool()
async def create_custom_audience(
    act_id: str,
    hashed_content: str,
    audience_name: str,
    description: Optional[str] = None
) -> Dict:
    """Creates a custom audience from content containing pre-hashed phone numbers.
    
    Args:
        act_id (str): The ad account ID (format: act_<id>)
        hashed_content (str): Content containing pre-hashed phone numbers (CSV format)
        audience_name (str): Name for the custom audience
        description (Optional[str]): Description for the custom audience
        
    Returns:
        Dict: Response from the Facebook API containing the created audience details
    """
    access_token = _get_fb_access_token()
    
    # First create the custom audience container
    if not act_id.startswith("act_"):
        act_id = f"act_{act_id}"
        
    create_audience_url = f"{FB_GRAPH_URL}/{act_id}/customaudiences"
    audience_params = {
        'access_token': access_token,
    }
    
    audience_data = {
        'name': audience_name,
        'subtype': 'CUSTOM',
        'customer_file_source': 'USER_PROVIDED_ONLY',
      }
    
    if description:
        audience_data['description'] = description

    audience_response = await _make_graph_api_call(
        create_audience_url, 
        params=audience_params,
        data=audience_data,
        method='POST'
    )
    
    if not audience_response or 'error' in audience_response:
        error_msg = audience_response.get('error', {}).get('message', 'Unknown error') if audience_response else 'Failed to create audience'
        return {"error": f"Failed to create custom audience: {error_msg}"}
        
    audience_id = audience_response['id']
    
    # Process pre-hashed phone numbers from content
    hashed_phones = [line.strip().split(',')[1].strip() for line in hashed_content.splitlines() if line.strip() and ',' in line]
    
    # Skip header if present
    if hashed_phones and hashed_phones[0].lower() == 'mobile_number_hash':
        hashed_phones = hashed_phones[1:]
    
    # Add users to the audience
    add_users_url = f"{FB_GRAPH_URL}/{audience_id}/users"
    users_params = {
        'access_token': access_token
    }
    
    users_data = {
        'payload': {
            'schema': ['PHONE_SHA256'],
            'data': [[phone] for phone in hashed_phones]
        }
    }
    
    response = await _make_graph_api_call(
        add_users_url, 
        params=users_params, 
        method='POST',
        data=users_data
    )
    
    return response or {"error": "Failed to add users to custom audience"}

@mcp.tool()
async def create_ad_campaign(
    act_id: str,
    name: str,
    objective: str,
    custom_audience_id: str,
    daily_budget: float,
    bid_amount: Optional[float] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    targeting: Optional[Dict] = None,
    status: str = 'PAUSED',
    campaign_fields: Optional[List[str]] = None,
    adset_fields: Optional[List[str]] = None,
    ad_fields: Optional[List[str]] = None,
    page_id: str = None,
    ad_link: str = None,
    ad_message: str = None,
    ad_title: Optional[str] = None
) -> Dict:
    """Creates a complete ad campaign targeting a custom audience.
    
    Args:
        act_id (str): The ad account ID (format: act_<id>)
        name (str): Name for the campaign
        objective (str): Campaign objective (e.g., 'REACH', 'LINK_CLICKS', etc.)
        custom_audience_id (str): ID of the custom audience to target
        daily_budget (float): Daily budget in account currency
        bid_amount (Optional[float]): Bid amount for the ad set
        start_time (Optional[str]): Start time in ISO format (YYYY-MM-DDThh:mm:ss+0000)
        end_time (Optional[str]): End time in ISO format (YYYY-MM-DDThh:mm:ss+0000)
        targeting (Optional[Dict]): Additional targeting specifications
        status (str): Initial status of the campaign ('ACTIVE' or 'PAUSED')
        campaign_fields (Optional[List[str]]): Fields to return for the created campaign
        adset_fields (Optional[List[str]]): Fields to return for the created ad set
        ad_fields (Optional[List[str]]): Fields to return for the created ad
        page_id (str): The Facebook Page ID to use for the ad
        ad_link (str): The URL where the ad will direct users
        ad_message (str): The main message/body text of the ad
        ad_title (Optional[str]): The title of the ad. If None, uses campaign name
        
    Returns:
        Dict: Response containing the created campaign, ad set, and ad details
    """
    access_token = _get_fb_access_token()
    
    # Create campaign
    campaign_url = f"{FB_GRAPH_URL}/{act_id}/campaigns"
    campaign_params = {
        'access_token': access_token,
        'fields': ','.join(campaign_fields) if campaign_fields else None
    }
    
    campaign_data = {
        'name': name,
        'objective': objective,
        'status': status,
        'special_ad_categories': ['NONE'],
        'daily_budget': int(daily_budget * 100)  # Convert to cents
    }
    
    campaign_response = await _make_graph_api_call(
        campaign_url, 
        params=campaign_params, 
        method='POST',
        data=campaign_data
    )
    
    if not campaign_response:
        return {"error": "Failed to create campaign"}
        
    campaign_id = campaign_response['id']
    
    # Create ad set
    adset_url = f"{FB_GRAPH_URL}/{act_id}/adsets"
    adset_params = {
        'access_token': access_token,
        'fields': ','.join(adset_fields) if adset_fields else None
    }
    
    # Base targeting including custom audience
    base_targeting = {
        'custom_audiences': [{'id': custom_audience_id}]
    }
    
    # Merge with additional targeting if provided
    if targeting:
        base_targeting.update(targeting)
    
    adset_data = {
        'name': f"{name} Ad Set",
        'campaign_id': campaign_id,
        'daily_budget': int(daily_budget * 100),
        'billing_event': 'IMPRESSIONS',
        'optimization_goal': objective,
        'bid_amount': int(bid_amount * 100) if bid_amount else None,
        'targeting': base_targeting,
        'status': status
    }
    
    if start_time:
        adset_data['start_time'] = start_time
    if end_time:
        adset_data['end_time'] = end_time
    
    adset_response = await _make_graph_api_call(
        adset_url, 
        params=adset_params, 
        method='POST',
        data=adset_data
    )
    
    if not adset_response:
        return {"error": "Failed to create ad set"}
        
    adset_id = adset_response['id']
    
    # Create a basic ad
    ad_url = f"{FB_GRAPH_URL}/{act_id}/ads"
    ad_params = {
        'access_token': access_token,
        'fields': ','.join(ad_fields) if ad_fields else None
    }
    
    ad_data = {
        'name': f"{name} Ad",
        'adset_id': adset_id,
        'status': status,
        'creative': {
            'title': ad_title or name,
            'body': ad_message or 'Ad created via MCP server',
            'object_story_spec': {
                'page_id': page_id,
                'link_data': {
                    'link': ad_link,
                    'message': ad_message or 'Ad message'
                }
            }
        }
    }
    
    ad_response = await _make_graph_api_call(
        ad_url, 
        params=ad_params, 
        method='POST',
        data=ad_data
    )
    
    if not ad_response:
        return {"error": "Failed to create ad"}
    
    return {
        'campaign': campaign_response,
        'adset': adset_response,
        'ad': ad_response
    }

