"""
Startup Discovery Module
Automatically searches for startups from various sources and processes them.
"""

import os
import json
import logging
import requests
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Read environment variables (main.py loads .env BEFORE importing this module)
# Using functions to ensure env vars are read at runtime, not import time
def _get_demo_mode():
    return os.getenv("DEMO_MODE", "true").lower() == "true"

def _get_auto_search_enabled():
    return os.getenv("AUTO_SEARCH_STARTUPS", "false").lower() == "true"

def _get_search_interval_hours():
    return int(os.getenv("SEARCH_INTERVAL_HOURS", "24"))

def _get_startup_search_sources():
    return os.getenv("STARTUP_SEARCH_SOURCES", "demo,producthunt").split(",")

def _get_default_source_limit():
    return int(os.getenv("STARTUP_DISCOVERY_LIMIT", "15"))

# Module-level variables that read env vars (will be read after .env is loaded by main.py)
DEMO_MODE = _get_demo_mode()
AUTO_SEARCH_ENABLED = _get_auto_search_enabled()
SEARCH_INTERVAL_HOURS = _get_search_interval_hours()
STARTUP_SEARCH_SOURCES = _get_startup_search_sources()
DEFAULT_SOURCE_LIMIT = _get_default_source_limit()

# Debug logging for environment variables
def _log_env_status():
    """Log environment variable status for debugging."""
    logger.debug(f"[ENV] DEMO_MODE={os.getenv('DEMO_MODE', 'not set')} -> {DEMO_MODE}")
    logger.debug(f"[ENV] AUTO_SEARCH_STARTUPS={os.getenv('AUTO_SEARCH_STARTUPS', 'not set')} -> {AUTO_SEARCH_ENABLED}")
    logger.debug(f"[ENV] SEARCH_INTERVAL_HOURS={os.getenv('SEARCH_INTERVAL_HOURS', 'not set')} -> {SEARCH_INTERVAL_HOURS}")
    logger.debug(f"[ENV] STARTUP_SEARCH_SOURCES={os.getenv('STARTUP_SEARCH_SOURCES', 'not set')} -> {STARTUP_SEARCH_SOURCES}")

# Log environment status when module is imported
_log_env_status()

# Debug logging helper
def debug_log(message: str, level: str = "INFO"):
    """Helper function for consistent debug logging."""
    if level == "DEBUG":
        logger.debug(f"[STARTUP_DISCOVERY] {message}")
    elif level == "INFO":
        logger.info(f"[STARTUP_DISCOVERY] {message}")
    elif level == "WARNING":
        logger.warning(f"[STARTUP_DISCOVERY] {message}")
    elif level == "ERROR":
        logger.error(f"[STARTUP_DISCOVERY] {message}")


def discover_startups_from_product_hunt(limit: int = DEFAULT_SOURCE_LIMIT) -> List[Dict[str, Any]]:
    """
    Discover startups from Product Hunt using their GraphQL API.
    
    Args:
        limit: Maximum number of startups to return
        
    Returns:
        List of startup data dictionaries
    """
    debug_log(f"Starting Product Hunt discovery (limit={limit})")
    
    if DEMO_MODE:
        debug_log("DEMO_MODE=true: Simulating Product Hunt startup discovery", "WARNING")
        return _simulate_product_hunt_startups(limit)
    
    api_token = os.getenv("PRODUCT_HUNT_API_TOKEN")
    debug_log(f"Product Hunt API token present: {bool(api_token)}")
    
    try:
        # Product Hunt GraphQL API endpoint
        url = "https://api.producthunt.com/v2/api/graphql"
        debug_log(f"Calling Product Hunt API: {url}")
        
        # GraphQL query to get today's top products
        # Note: Product Hunt API v2 schema - makers is a single user object, not edges
        query = """
        query($first: Int!) {
          posts(first: $first, order: VOTES) {
            edges {
              node {
                id
                name
                tagline
                description
                website
                votesCount
                commentsCount
                createdAt
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
                user {
                  name
                  profileImage
                }
              }
            }
          }
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # If API token is provided, use it
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        
        variables = {"first": min(limit, 50)}  # Product Hunt allows up to 50 per request
        debug_log(f"Product Hunt query variables: {variables}")
        debug_log(f"Request headers: {list(headers.keys())}")
        
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=30
        )
        
        debug_log(f"Product Hunt API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            debug_log(f"Product Hunt API response received, parsing data...")
            
            posts = data.get("data", {}).get("posts", {}).get("edges", [])
            debug_log(f"Found {len(posts)} posts from Product Hunt API")
            
            if not posts:
                debug_log("No posts found in Product Hunt response", "WARNING")
                debug_log(f"Response data structure: {list(data.keys())}", "DEBUG")
            
            startups = []
            for idx, edge in enumerate(posts[:limit], 1):
                debug_log(f"Processing Product Hunt post {idx}/{min(len(posts), limit)}")
                node = edge.get("node", {})
                
                # Extract topics/categories
                topics = []
                for topic_edge in node.get("topics", {}).get("edges", []):
                    topics.append(topic_edge.get("node", {}).get("name", ""))
                
                # Extract user/maker (Product Hunt API v2 uses 'user' not 'makers')
                makers = []
                user = node.get("user", {})
                if user and user.get("name"):
                    makers.append({
                        "name": user.get("name", ""),
                        "role": "Founder"
                    })
                
                # Determine stage based on votes and engagement
                votes = node.get("votesCount", 0)
                if votes > 500:
                    stage = "Series A"
                elif votes > 200:
                    stage = "Seed"
                else:
                    stage = "Pre-Seed"
                
                startup_name = node.get("name", "Unknown")
                debug_log(f"  - Processing: {startup_name}")
                debug_log(f"    Votes: {votes}, Comments: {node.get('commentsCount', 0)}", "DEBUG")
                debug_log(f"    Topics: {topics[:3] if topics else 'None'}", "DEBUG")
                debug_log(f"    Makers: {len(makers)}", "DEBUG")
                
                startup = {
                    "name": startup_name,
                    "sector": topics[0] if topics else "Technology",
                    "stage": stage,
                    "description": node.get("description") or node.get("tagline", ""),
                    "team": makers if makers else [{"name": "Founder", "role": "Founder"}],
                    "metrics": {
                        "votes": votes,
                        "comments": node.get("commentsCount", 0),
                        "engagement_score": votes + (node.get("commentsCount", 0) * 2)
                    },
                    "ask": {
                        "amount": None,  # Product Hunt doesn't provide funding info
                        "valuation": None,
                        "use_of_funds": "Not specified"
                    },
                    "market": {
                        "size": f"Market size data not available from Product Hunt",
                        "competition": f"Competing in {', '.join(topics[:3]) if topics else 'Technology'} space"
                    },
                    "website": node.get("website"),
                    "source": "producthunt",
                    "source_id": node.get("id")
                }
                
                startups.append(startup)
                debug_log(f"  ✓ Added startup: {startup_name}")
            
            debug_log(f"Successfully fetched {len(startups)} startups from Product Hunt", "INFO")
            return startups
        else:
            debug_log(f"Product Hunt API returned error status {response.status_code}", "ERROR")
            debug_log(f"Response body: {response.text[:500]}", "DEBUG")
            if not api_token:
                debug_log("Tip: Set PRODUCT_HUNT_API_TOKEN for better rate limits", "INFO")
            debug_log("Falling back to simulated Product Hunt data", "WARNING")
            return _simulate_product_hunt_startups(limit)
            
    except requests.exceptions.Timeout as e:
        debug_log(f"Product Hunt API timeout: {e}", "ERROR")
        debug_log("Falling back to simulated Product Hunt data", "WARNING")
        return _simulate_product_hunt_startups(limit)
    except requests.exceptions.RequestException as e:
        debug_log(f"Product Hunt API request error: {e}", "ERROR")
        debug_log(f"Error type: {type(e).__name__}", "DEBUG")
        debug_log("Falling back to simulated Product Hunt data", "WARNING")
        return _simulate_product_hunt_startups(limit)
    except Exception as e:
        debug_log(f"Unexpected error fetching from Product Hunt: {e}", "ERROR")
        debug_log(f"Error type: {type(e).__name__}", "DEBUG")
        import traceback
        debug_log(f"Traceback: {traceback.format_exc()}", "DEBUG")
        debug_log("Falling back to simulated Product Hunt data", "WARNING")
        return _simulate_product_hunt_startups(limit)


def discover_startups_from_crunchbase(limit: int = DEFAULT_SOURCE_LIMIT) -> List[Dict[str, Any]]:
    """
    Discover startups from Crunchbase using their API.
    
    Args:
        limit: Maximum number of startups to return
        
    Returns:
        List of startup data dictionaries
    """
    debug_log(f"Starting Crunchbase discovery (limit={limit})")
    
    if DEMO_MODE:
        debug_log("DEMO_MODE=true: Simulating Crunchbase startup discovery", "WARNING")
        return _simulate_crunchbase_startups(limit)
    
    api_key = os.getenv("CRUNCHBASE_API_KEY")
    debug_log(f"Crunchbase API key present: {bool(api_key)}")
    
    if not api_key:
        debug_log("CRUNCHBASE_API_KEY not set, using simulation", "WARNING")
        return _simulate_crunchbase_startups(limit)
    
    try:
        # Crunchbase API v4 endpoint
        # Search for organizations that are startups (funding rounds, recent)
        url = "https://api.crunchbase.com/v4/searches/organizations"
        debug_log(f"Calling Crunchbase API: {url}")
        
        headers = {
            "X-cb-user-key": api_key,
            "Content-Type": "application/json"
        }
        debug_log(f"Crunchbase request headers: {list(headers.keys())}")
        
        # Query for recently funded startups
        query_data = {
            "field_ids": [
                "identifier",
                "name",
                "categories",
                "short_description",
                "website",
                "founded_on",
                "funding_total",
                "num_funding_rounds",
                "last_funding_on",
                "last_funding_type"
            ],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "funding_total",
                    "operator_id": "gte",
                    "values": ["100000"]  # At least $100k funding
                },
                {
                    "type": "predicate",
                    "field_id": "last_funding_on",
                    "operator_id": "gte",
                    "values": ["2023-01-01"]  # Funded in last 2 years
                }
            ],
            "limit": min(limit, 25),  # Crunchbase API limit
            "order": [
                {
                    "field_id": "last_funding_on",
                    "sort": "desc"
                }
            ]
        }
        
        debug_log(f"Crunchbase query: funding_total >= $100k, last_funding >= 2023-01-01", "DEBUG")
        debug_log(f"Crunchbase query limit: {query_data['limit']}", "DEBUG")
        
        response = requests.post(
            url,
            json=query_data,
            headers=headers,
            timeout=30
        )
        
        debug_log(f"Crunchbase API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            debug_log(f"Crunchbase API response received, parsing data...")
            
            entities = data.get("entities", [])
            debug_log(f"Found {len(entities)} entities from Crunchbase API")
            
            if not entities:
                debug_log("No entities found in Crunchbase response", "WARNING")
                debug_log(f"Response data structure: {list(data.keys())}", "DEBUG")
            
            startups = []
            for idx, entity in enumerate(entities[:limit], 1):
                debug_log(f"Processing Crunchbase entity {idx}/{min(len(entities), limit)}")
                properties = entity.get("properties", {})
                identifier = entity.get("identifier", {})
                
                # Extract categories
                categories = properties.get("categories", [])
                sector = categories[0] if categories else "Technology"
                
                # Determine stage from funding
                funding_total = properties.get("funding_total", {}).get("value", 0)
                num_rounds = properties.get("num_funding_rounds", {}).get("value", 0)
                
                startup_name = properties.get("name", "Unknown")
                debug_log(f"  - Processing: {startup_name}")
                debug_log(f"    Funding total: ${funding_total:,}, Rounds: {num_rounds}", "DEBUG")
                debug_log(f"    Sector: {sector}", "DEBUG")
                
                if funding_total > 10000000:
                    stage = "Series A"
                elif funding_total > 1000000:
                    stage = "Seed"
                else:
                    stage = "Pre-Seed"
                
                debug_log(f"    Determined stage: {stage}", "DEBUG")
                
                # Get funding info
                last_funding_type = properties.get("last_funding_type", "")
                
                startup = {
                    "name": startup_name,
                    "sector": sector,
                    "stage": stage,
                    "description": properties.get("short_description", ""),
                    "team": [],  # Crunchbase API doesn't always include founders in search
                    "metrics": {
                        "funding_total": funding_total,
                        "num_funding_rounds": num_rounds,
                        "last_funding_date": properties.get("last_funding_on", {}).get("value", "")
                    },
                    "ask": {
                        "amount": None,  # Would need to query individual organization for current ask
                        "valuation": None,
                        "use_of_funds": "Not specified"
                    },
                    "market": {
                        "size": f"Operating in {sector} sector",
                        "competition": "Market competition data available via detailed query"
                    },
                    "website": properties.get("website", {}).get("value", ""),
                    "founded_on": properties.get("founded_on", {}).get("value", ""),
                    "source": "crunchbase",
                    "source_id": identifier.get("uuid", "")
                }
                
                startups.append(startup)
                debug_log(f"  ✓ Added startup: {startup_name}")
            
            debug_log(f"Successfully fetched {len(startups)} startups from Crunchbase", "INFO")
            return startups
        else:
            debug_log(f"Crunchbase API returned error status {response.status_code}", "ERROR")
            debug_log(f"Response body: {response.text[:500]}", "DEBUG")
            debug_log("Falling back to simulated Crunchbase data", "WARNING")
            return _simulate_crunchbase_startups(limit)
            
    except requests.exceptions.Timeout as e:
        debug_log(f"Crunchbase API timeout: {e}", "ERROR")
        debug_log("Falling back to simulated Crunchbase data", "WARNING")
        return _simulate_crunchbase_startups(limit)
    except requests.exceptions.RequestException as e:
        debug_log(f"Crunchbase API request error: {e}", "ERROR")
        debug_log(f"Error type: {type(e).__name__}", "DEBUG")
        debug_log("Falling back to simulated Crunchbase data", "WARNING")
        return _simulate_crunchbase_startups(limit)
    except Exception as e:
        debug_log(f"Unexpected error fetching from Crunchbase: {e}", "ERROR")
        debug_log(f"Error type: {type(e).__name__}", "DEBUG")
        import traceback
        debug_log(f"Traceback: {traceback.format_exc()}", "DEBUG")
        debug_log("Falling back to simulated Crunchbase data", "WARNING")
        return _simulate_crunchbase_startups(limit)


def discover_startups_from_demo_source(limit: int = DEFAULT_SOURCE_LIMIT) -> List[Dict[str, Any]]:
    """
    Generate demo startup data for testing.
    
    Args:
        limit: Maximum number of startups to return
        
    Returns:
        List of startup data dictionaries
    """
    logger.info("Generating demo startup data")
    
    demo_startups = [
        {
            "name": "AIFlow",
            "sector": "Enterprise Software",
            "stage": "Seed",
            "description": "AIFlow provides intelligent workflow automation for enterprises. Their AI-powered platform helps companies automate complex business processes, reducing manual work by up to 80%.",
            "team": [
                {"name": "Sarah Chen", "role": "CEO", "background": "Former VP at Salesforce"},
                {"name": "Michael Park", "role": "CTO", "background": "Ex-Google, 15 years ML experience"}
            ],
            "metrics": {
                "mrr": 120000,
                "growth_rate": 25,
                "customers": 45,
                "runway_months": 12
            },
            "ask": {
                "amount": 3000000,
                "valuation": 15000000,
                "use_of_funds": "Engineering (50%), Sales (30%), Marketing (20%)"
            },
            "market": {
                "size": "Workflow automation market projected to reach $25B by 2028",
                "competition": "Competing with Zapier, but focused on enterprise AI capabilities"
            }
        },
        {
            "name": "GreenTech Solutions",
            "sector": "Clean Energy",
            "stage": "Series A",
            "description": "GreenTech Solutions develops advanced solar panel technology with 40% higher efficiency than traditional panels. Their proprietary nanotechnology enables better energy capture and longer lifespan.",
            "team": [
                {"name": "Dr. Emily Rodriguez", "role": "CEO", "background": "PhD Materials Science, MIT"},
                {"name": "James Liu", "role": "COO", "background": "Former Tesla manufacturing lead"}
            ],
            "metrics": {
                "mrr": 450000,
                "growth_rate": 18,
                "customers": 120,
                "runway_months": 24
            },
            "ask": {
                "amount": 10000000,
                "valuation": 50000000,
                "use_of_funds": "Manufacturing scale-up (60%), R&D (25%), Sales (15%)"
            },
            "market": {
                "size": "Solar panel market expected to reach $200B by 2030",
                "competition": "Differentiated by efficiency gains and lower cost per watt"
            }
        },
        {
            "name": "HealthVault",
            "sector": "Healthcare Technology",
            "stage": "Seed",
            "description": "HealthVault is building a decentralized health records platform using blockchain technology. Patients own their data and can securely share it with healthcare providers.",
            "team": [
                {"name": "Dr. Robert Kim", "role": "CEO", "background": "MD, Former healthcare IT consultant"},
                {"name": "Lisa Wang", "role": "CTO", "background": "Blockchain expert, ex-Consensys"}
            ],
            "metrics": {
                "mrr": 85000,
                "growth_rate": 30,
                "customers": 28,
                "runway_months": 15
            },
            "ask": {
                "amount": 5000000,
                "valuation": 20000000,
                "use_of_funds": "Product development (45%), Compliance (25%), Sales (30%)"
            },
            "market": {
                "size": "Healthcare data management market growing to $50B by 2027",
                "competition": "First-mover advantage in blockchain-based health records"
            }
        },
        {
            "name": "EduLearn AI",
            "sector": "EdTech",
            "stage": "Series A",
            "description": "EduLearn AI provides personalized learning experiences using advanced AI. Their platform adapts to each student's learning style and pace, improving outcomes by 35%.",
            "team": [
                {"name": "Dr. Maria Garcia", "role": "CEO", "background": "Former Stanford Education Professor"},
                {"name": "David Thompson", "role": "CTO", "background": "Ex-Khan Academy, AI researcher"}
            ],
            "metrics": {
                "mrr": 320000,
                "growth_rate": 22,
                "customers": 85,
                "runway_months": 18
            },
            "ask": {
                "amount": 8000000,
                "valuation": 40000000,
                "use_of_funds": "Content development (40%), AI R&D (35%), Sales (25%)"
            },
            "market": {
                "size": "EdTech market projected to reach $377B by 2028",
                "competition": "Differentiated by AI personalization and proven outcomes"
            }
        },
        {
            "name": "FoodChain",
            "sector": "Food Technology",
            "stage": "Seed",
            "description": "FoodChain uses blockchain to provide complete supply chain transparency for food products. Consumers can trace food from farm to table, ensuring quality and safety.",
            "team": [
                {"name": "Alex Johnson", "role": "CEO", "background": "Former Whole Foods executive"},
                {"name": "Priya Patel", "role": "CTO", "background": "Blockchain developer, ex-IBM"}
            ],
            "metrics": {
                "mrr": 95000,
                "growth_rate": 28,
                "customers": 35,
                "runway_months": 14
            },
            "ask": {
                "amount": 4000000,
                "valuation": 18000000,
                "use_of_funds": "Platform development (50%), Partnerships (30%), Marketing (20%)"
            },
            "market": {
                "size": "Food traceability market growing to $22B by 2027",
                "competition": "Unique blockchain approach with strong early adoption"
            }
        }
    ]
    
    return demo_startups[:limit]


def _simulate_product_hunt_startups(limit: int) -> List[Dict[str, Any]]:
    """Simulate Product Hunt startup discoveries."""
    return discover_startups_from_demo_source(limit)


def _simulate_crunchbase_startups(limit: int) -> List[Dict[str, Any]]:
    """Simulate Crunchbase startup discoveries."""
    return discover_startups_from_demo_source(limit)


def discover_startups_from_ycombinator(limit: int = DEFAULT_SOURCE_LIMIT) -> List[Dict[str, Any]]:
    """
    Discover startups from Y Combinator (using public data).
    
    Args:
        limit: Maximum number of startups to return
        
    Returns:
        List of startup data dictionaries
    """
    try:
        # Y Combinator has a public API/endpoint for their portfolio
        # Using their public companies list
        url = "https://api.ycombinator.com/companies"  # This is a placeholder - YC doesn't have public API
        
        # Alternative: Scrape or use YC's public directory
        # For now, we'll use a known approach: YC publishes batch lists
        
        # Since YC doesn't have a public API, we'll fetch from their public directory
        # This is a simplified implementation - in production you might want to scrape
        # or use a third-party service that aggregates YC data
        
        logger.info("Y Combinator API not publicly available, using demo data")
        return _simulate_ycombinator_startups(limit)
        
    except Exception as e:
        logger.error(f"Error fetching from Y Combinator: {e}")
        return []


def _simulate_ycombinator_startups(limit: int) -> List[Dict[str, Any]]:
    """Generate Y Combinator-style startup data."""
    yc_startups = [
        {
            "name": "AIWorkflow",
            "sector": "Enterprise AI",
            "stage": "Seed",
            "description": "YC S23 batch company building AI-powered workflow automation for enterprises. Raised $2M seed round.",
            "team": [
                {"name": "Founder Team", "role": "YC Batch S23", "background": "Y Combinator"}
            ],
            "metrics": {
                "mrr": 150000,
                "growth_rate": 30,
                "customers": 50,
                "runway_months": 18
            },
            "ask": {
                "amount": 3000000,
                "valuation": 15000000,
                "use_of_funds": "Product development and sales expansion"
            },
            "market": {
                "size": "Enterprise automation market",
                "competition": "Competing with established players"
            },
            "source": "ycombinator"
        }
    ]
    return yc_startups[:limit]


def discover_startups(sources: Optional[List[str]] = None, limit_per_source: int = DEFAULT_SOURCE_LIMIT) -> List[Dict[str, Any]]:
    """
    Discover startups from multiple sources.
    
    Args:
        sources: List of sources to search (defaults to STARTUP_SEARCH_SOURCES)
        limit_per_source: Maximum startups per source
        
    Returns:
        List of startup data dictionaries
    """
    debug_log("=" * 60)
    debug_log("STARTING STARTUP DISCOVERY PROCESS")
    debug_log(f"DEMO_MODE: {DEMO_MODE}")
    debug_log(f"Limit per source: {limit_per_source}")
    
    if sources is None:
        sources = STARTUP_SEARCH_SOURCES
        debug_log(f"Using default sources: {sources}")
    else:
        debug_log(f"Using provided sources: {sources}")
    
    all_startups = []
    seen_names = set()
    source_results = {}
    
    for idx, source in enumerate(sources, 1):
        source = source.strip().lower()
        debug_log(f"\n[{idx}/{len(sources)}] Processing source: {source}")
        
        try:
            source_start_time = datetime.now()
            
            if source == "producthunt":
                startups = discover_startups_from_product_hunt(limit_per_source)
            elif source == "crunchbase":
                startups = discover_startups_from_crunchbase(limit_per_source)
            elif source == "ycombinator" or source == "yc":
                startups = discover_startups_from_ycombinator(limit_per_source)
            elif source == "demo":
                startups = discover_startups_from_demo_source(limit_per_source)
            else:
                debug_log(f"Unknown startup source: {source}", "WARNING")
                source_results[source] = {"count": 0, "error": "Unknown source"}
                continue
            
            source_duration = (datetime.now() - source_start_time).total_seconds()
            debug_log(f"Source '{source}' returned {len(startups)} startups in {source_duration:.2f}s")
            
            # Deduplicate by name
            added_count = 0
            skipped_count = 0
            for startup in startups:
                startup_name = startup.get("name")
                if startup_name:
                    if startup_name not in seen_names:
                        all_startups.append(startup)
                        seen_names.add(startup_name)
                        added_count += 1
                        debug_log(f"  ✓ Added: {startup_name} (from {startup.get('source', 'unknown')})", "DEBUG")
                    else:
                        skipped_count += 1
                        debug_log(f"  ⊗ Skipped duplicate: {startup_name}", "DEBUG")
                else:
                    debug_log(f"  ⊗ Skipped startup without name", "WARNING")
            
            source_results[source] = {
                "count": len(startups),
                "added": added_count,
                "skipped": skipped_count,
                "duration": source_duration
            }
            debug_log(f"Source '{source}' summary: {added_count} added, {skipped_count} skipped")
                    
        except Exception as e:
            debug_log(f"Error discovering startups from {source}: {e}", "ERROR")
            debug_log(f"Error type: {type(e).__name__}", "DEBUG")
            import traceback
            debug_log(f"Traceback: {traceback.format_exc()}", "DEBUG")
            source_results[source] = {"count": 0, "error": str(e)}
            continue
    
    debug_log("\n" + "=" * 60)
    debug_log("DISCOVERY SUMMARY")
    debug_log(f"Total unique startups discovered: {len(all_startups)}")
    debug_log(f"Sources processed: {len(sources)}")
    for source, result in source_results.items():
        if "error" in result:
            debug_log(f"  {source}: ERROR - {result['error']}")
        else:
            debug_log(f"  {source}: {result['added']} added ({result['count']} total, {result['skipped']} skipped) in {result['duration']:.2f}s")
    debug_log("=" * 60)
    
    return all_startups


def process_discovered_startup(startup_data: Dict[str, Any], use_direct_call: bool = True) -> Optional[Dict[str, Any]]:
    """
    Process a discovered startup through the agent pipeline.
    
    Args:
        startup_data: Startup data dictionary
        use_direct_call: If True, call agent functions directly instead of subprocess (faster, no hangs)
        
    Returns:
        Result dictionary with proposal_id and status, or None if failed
    """
    startup_name = startup_data.get("name", "Unknown")
    debug_log(f"\nProcessing startup: {startup_name}")
    debug_log(f"  Source: {startup_data.get('source', 'unknown')}")
    debug_log(f"  Sector: {startup_data.get('sector', 'unknown')}")
    debug_log(f"  Stage: {startup_data.get('stage', 'unknown')}")
    debug_log(f"  Method: {'direct call' if use_direct_call else 'subprocess'}")
    
    # Try direct function call first (more reliable, no subprocess issues)
    if use_direct_call:
        try:
            debug_log(f"  Attempting direct function call to agent...")
            # Import agent functions directly
            import sys
            agent_module_path = Path(__file__).parent.parent.parent / "spoon_agent"
            if str(agent_module_path) not in sys.path:
                sys.path.insert(0, str(agent_module_path))
            
            from main import process_startup_data
            # Import direct submission function to bypass HTTP
            # Use relative import since we're in the same package
            from .main import submit_proposal_direct
            
            process_start_time = datetime.now()
            # Pass direct submission callback to avoid HTTP timeout
            result = process_startup_data(startup_data, submit_callback=submit_proposal_direct)
            process_duration = (datetime.now() - process_start_time).total_seconds()
            
            debug_log(f"  ✓ Successfully processed via direct call in {process_duration:.2f}s", "INFO")
            debug_log(f"  Proposal ID: {result.get('proposal_id')}", "DEBUG")
            debug_log(f"  IPFS CID: {result.get('ipfs_cid')}", "DEBUG")
            
            return {
                "status": "success",
                "startup_name": startup_name,
                "proposal_id": result.get("proposal_id"),
                "ipfs_cid": result.get("ipfs_cid")
            }
        except ImportError as e:
            debug_log(f"  Direct call failed (ImportError): {e}", "WARNING")
            debug_log(f"  Falling back to subprocess method...", "INFO")
        except Exception as e:
            debug_log(f"  Direct call failed: {e}", "ERROR")
            debug_log(f"  Error type: {type(e).__name__}", "DEBUG")
            import traceback
            debug_log(f"  Traceback: {traceback.format_exc()}", "DEBUG")
            debug_log(f"  Falling back to subprocess method...", "INFO")
    
    # Fallback to subprocess method
    try:
        # Get the path to the agent main.py
        agent_path = Path(__file__).parent.parent.parent / "spoon_agent" / "main.py"
        debug_log(f"  Agent path: {agent_path}")
        
        if not agent_path.exists():
            debug_log(f"Agent not found at {agent_path}", "ERROR")
            return None
        
        # Create temporary JSON file with startup data
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(startup_data, tmp, indent=2)
            tmp_path = tmp.name
        
        debug_log(f"  Created temp file: {tmp_path}", "DEBUG")
        
        try:
            # Run the agent to process the startup
            debug_log(f"  Running agent subprocess...")
            debug_log(f"  Command: {sys.executable} {agent_path} --input {tmp_path}", "DEBUG")
            debug_log(f"  Working directory: {agent_path.parent.parent}", "DEBUG")
            process_start_time = datetime.now()
            
            # Use Popen for better control and monitoring
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(agent_path),
                    "--input", tmp_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                stdin=subprocess.DEVNULL,  # Prevent waiting for stdin input
                cwd=str(agent_path.parent.parent),
                bufsize=0,  # Unbuffered for immediate output
                env=os.environ.copy()  # Pass environment variables
            )
            
            debug_log(f"  Process started with PID: {process.pid}", "DEBUG")
            
            # Wait for completion with timeout and periodic status updates
            timeout_seconds = 120  # Reduced to 2 minutes (LLM calls should complete faster)
            check_interval = 2  # Check every 2 seconds for faster response
            elapsed = 0
            
            while elapsed < timeout_seconds:
                returncode = process.poll()
                if returncode is not None:
                    # Process completed
                    debug_log(f"  Process completed (returncode={returncode})", "DEBUG")
                    break
                time.sleep(check_interval)
                elapsed += check_interval
                if elapsed % 20 == 0:  # Log every 20 seconds
                    debug_log(f"  Agent still running... ({elapsed}s elapsed, PID: {process.pid})", "DEBUG")
            
            # Check if process is still running
            if process.poll() is None:
                debug_log(f"  Agent process exceeded timeout ({timeout_seconds}s), terminating...", "WARNING")
                try:
                    process.terminate()
                    # Wait up to 3 seconds for graceful termination
                    for _ in range(6):
                        if process.poll() is not None:
                            break
                        time.sleep(0.5)
                    
                    if process.poll() is None:
                        debug_log(f"  Process did not terminate gracefully, killing...", "WARNING")
                        process.kill()
                        # Use wait with timeout to avoid hanging
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            pass
                except Exception as e:
                    debug_log(f"  Error terminating process: {e}", "ERROR")
                    try:
                        process.kill()
                    except:
                        pass
                
                # Return timeout error instead of raising
                return {
                    "status": "timeout",
                    "startup_name": startup_name,
                    "error": f"Agent process exceeded {timeout_seconds}s timeout"
                }
            
            # Get output (process is already done, so communicate should return immediately)
            # Set a reasonable timeout for safety
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                # This shouldn't happen if process is done, but handle it anyway
                debug_log(f"  communicate() unexpectedly timed out", "WARNING")
                process.kill()
                stdout, stderr = process.communicate()
            
            returncode = process.returncode
            
            process_duration = (datetime.now() - process_start_time).total_seconds()
            debug_log(f"  Agent process completed in {process_duration:.2f}s")
            debug_log(f"  Return code: {returncode}")
            debug_log(f"  Stdout length: {len(stdout)} chars, Stderr length: {len(stderr)} chars", "DEBUG")
            
            # Create result object similar to subprocess.run
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr
            
            result = Result(returncode, stdout, stderr)
            
            if result.returncode == 0:
                debug_log(f"  ✓ Successfully processed startup: {startup_name}", "INFO")
                debug_log(f"  Agent stdout length: {len(result.stdout)} chars", "DEBUG")
                
                # Try to parse output if available
                # JSON might be mixed with log output, so extract it
                try:
                    # First try parsing the entire stdout
                    output_data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from mixed output
                    # Look for JSON object in stdout (starts with { and ends with })
                    import re
                    json_match = re.search(r'\{.*\}', result.stdout, re.DOTALL)
                    if json_match:
                        try:
                            output_data = json.loads(json_match.group())
                            debug_log(f"  Extracted JSON from mixed stdout output", "DEBUG")
                        except json.JSONDecodeError as e:
                            debug_log(f"  Could not parse extracted JSON: {e}", "DEBUG")
                            debug_log(f"  Agent stdout (first 500 chars): {result.stdout[:500]}", "DEBUG")
                            return {
                                "status": "success",
                                "startup_name": startup_data.get("name")
                            }
                    else:
                        debug_log(f"  No JSON found in stdout output", "DEBUG")
                        debug_log(f"  Agent stdout (first 500 chars): {result.stdout[:500]}", "DEBUG")
                        return {
                            "status": "success",
                            "startup_name": startup_data.get("name")
                        }
                
                # Successfully parsed JSON
                debug_log(f"  Parsed agent output: {list(output_data.keys())}", "DEBUG")
                return {
                    "status": "success",
                    "startup_name": startup_data.get("name"),
                    "proposal_id": output_data.get("proposal_id"),
                    "ipfs_cid": output_data.get("ipfs_cid")
                }
            else:
                debug_log(f"  ✗ Agent failed for {startup_name}", "ERROR")
                debug_log(f"  Agent stderr: {result.stderr[:500]}", "DEBUG")
                return {
                    "status": "failed",
                    "startup_name": startup_data.get("name"),
                    "error": result.stderr[:200]
                }
                
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout processing startup: {startup_data.get('name')}")
        return {
            "status": "timeout",
            "startup_name": startup_data.get("name")
        }
    except Exception as e:
        logger.error(f"Error processing startup {startup_data.get('name')}: {e}")
        return {
            "status": "error",
            "startup_name": startup_data.get("name"),
            "error": str(e)
        }


def discover_and_process_startups(
    sources: Optional[List[str]] = None,
    limit_per_source: int = DEFAULT_SOURCE_LIMIT,
    additional_fields: Optional[str] = None,
    auto_process: bool = True,
    status_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Discover startups and optionally process them through the agent.
    
    Args:
        sources: List of sources to search
        limit_per_source: Maximum startups per source
        auto_process: Whether to automatically process discovered startups
        
    Returns:
        Dictionary with discovery and processing results
    """
    overall_start_time = datetime.now()
    debug_log("\n" + "=" * 60)
    debug_log("STARTING STARTUP DISCOVERY AND PROCESSING")
    debug_log(f"Auto-process: {auto_process}")
    debug_log(f"Sources: {sources or STARTUP_SEARCH_SOURCES}")
    debug_log(f"Limit per source: {limit_per_source}")
    if additional_fields:
        preview = (additional_fields[:120] + "...") if len(additional_fields) > 120 else additional_fields
        debug_log(f"Additional fields provided: {preview}", "DEBUG")
    debug_log("=" * 60)
    
    def update_status(update: Dict[str, Any]):
        if status_callback:
            try:
                status_callback(update)
            except Exception as e:
                debug_log(f"Status callback error: {e}", "WARNING")
    
    # Discover startups
    discovery_start_time = datetime.now()
    startups = discover_startups(sources=sources, limit_per_source=limit_per_source)
    discovery_duration = (datetime.now() - discovery_start_time).total_seconds()
    
    debug_log(f"\nDiscovery phase completed in {discovery_duration:.2f}s")
    debug_log(f"Total startups discovered: {len(startups)}")
    
    results = {
        "discovered": len(startups),
        "processed": 0,
        "failed": 0,
        "startups": [],
        "discovery_duration": discovery_duration
    }
    
    if not auto_process:
        debug_log("Auto-process disabled, returning discovered startups only")
        results["startups"] = startups
        return results
    
    update_status({
        "status": "running",
        "discovered": len(startups),
        "processed": 0,
        "failed": 0
    })
    
    # Process each startup
    debug_log(f"\nStarting processing phase for {len(startups)} startups...")
    processing_start_time = datetime.now()
    
    for idx, startup in enumerate(startups, 1):
        startup_name = startup.get("name", "Unknown")
        debug_log(f"\n[{idx}/{len(startups)}] Processing: {startup_name}")
        
        startup_payload = dict(startup)
        if additional_fields:
            startup_payload["additional_fields"] = additional_fields
        
        process_result = process_discovered_startup(startup_payload)
        if process_result:
            status = process_result.get("status", "unknown")
            if status == "success":
                results["processed"] += 1
                debug_log(f"  ✓ Successfully processed: {startup_name}")
            else:
                results["failed"] += 1
                debug_log(f"  ✗ Failed to process: {startup_name} - {status}")
            results["startups"].append({
                "startup": startup_name,
                "result": process_result
            })
        else:
            results["failed"] += 1
            debug_log(f"  ✗ Processing returned None for: {startup_name}", "WARNING")
        
        update_status({
            "processed": results["processed"],
            "failed": results["failed"],
            "current": startup_name,
            "completed": idx,
            "total": len(startups)
        })
    
    processing_duration = (datetime.now() - processing_start_time).total_seconds()
    overall_duration = (datetime.now() - overall_start_time).total_seconds()
    
    results["processing_duration"] = processing_duration
    results["total_duration"] = overall_duration
    
    debug_log("\n" + "=" * 60)
    debug_log("DISCOVERY AND PROCESSING COMPLETE")
    debug_log(f"Total discovered: {results['discovered']}")
    debug_log(f"Successfully processed: {results['processed']}")
    debug_log(f"Failed: {results['failed']}")
    debug_log(f"Discovery time: {discovery_duration:.2f}s")
    debug_log(f"Processing time: {processing_duration:.2f}s")
    debug_log(f"Total time: {overall_duration:.2f}s")
    debug_log("=" * 60)
    
    update_status({
        "status": "completed",
        "discovered": results["discovered"],
        "processed": results["processed"],
        "failed": results["failed"],
        "processing_duration": processing_duration,
        "total_duration": overall_duration
    })
    
    return results

