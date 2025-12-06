"""
Research Agent for SpoonOS

This module provides a ResearchAgent that performs comprehensive research on crypto projects
using web search capabilities to gather and analyze information.
"""
import asyncio
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from ..tools.web_search import WebSearchTool

class ResearchFindings(BaseModel):
    """Model to store research findings about a crypto project."""
    project_name: str
    team: List[Dict[str, str]] = Field(default_factory=list, description="Team members and their roles")
    audits: List[Dict[str, str]] = Field(default_factory=list, description="Security audits and their findings")
    partnerships: List[Dict[str, str]] = Field(default_factory=list, description="Partnerships and collaborations")
    controversies: List[Dict[str, str]] = Field(default_factory=list, description="Known controversies or issues")
    rugpull_warnings: List[Dict[str, str]] = Field(default_factory=list, description="Any rugpull warnings or red flags")
    social_activity: Dict[str, Any] = Field(default_factory=dict, description="Social media presence and activity")
    roadmap: List[Dict[str, str]] = Field(default_factory=list, description="Project roadmap and progress items")
    summary: str = Field(default="", description="Concise summary of findings")

class ResearchAgent:
    """
    An agent that researches crypto projects by analyzing information from web searches.
    """
    
    def __init__(self, search_tool: Optional[WebSearchTool] = None):
        """Initialize the ResearchAgent with an optional WebSearchTool instance."""
        self.search_tool = search_tool or WebSearchTool()
        self.search_queries = {
            'team': [
                "{project} team members",
                "{project} founders and developers",
                "who created {project} cryptocurrency",
                "{project} core team background"
            ],
            'audits': [
                "{project} smart contract audit",
                "{project} security audit report",
                "{project} audit findings"
            ],
            'partnerships': [
                "{project} partnerships",
                "{project} collaborations",
                "{project} ecosystem partners"
            ],
            'controversies': [
                "{project} controversy",
                "{project} issues or problems",
                "{project} criticism"
            ],
            'rugpull_warnings': [
                "{project} rugpull warning",
                "{project} scam or legit",
                "{project} red flags"
            ],
            'social_activity': [
                "{project} community activity",
                "{project} social media presence",
                "{project} telegram discord twitter"
            ],
            'roadmap': [
                "{project} roadmap 2025",
                "{project} development updates",
                "{project} future plans"
            ]
        }
    
    async def _search_and_analyze(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """Perform a search and analyze the results."""
        try:
            results = await self.search_tool.search(query, num_results=max_results)
            return results
        except Exception as e:
            print(f"Error searching for '{query}': {str(e)}")
            return []
    
    async def _extract_team_info(self, project_name: str) -> List[Dict[str, str]]:
        """Extract team information from search results."""
        team_members = []
        for query in self.search_queries['team']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                # Simple extraction - in a real implementation, you'd want to use NLP here
                if any(term in result['content'].lower() for term in ['founder', 'ceo', 'cto', 'developer', 'team']):
                    team_members.append({
                        'source': result['url'],
                        'info': result['snippet'][:500]  # First 500 chars of snippet
                    })
                    if len(team_members) >= 5:  # Limit to top 5 team members
                        break
        return team_members
    
    async def _extract_audits(self, project_name: str) -> List[Dict[str, str]]:
        """Extract audit information from search results."""
        audits = []
        for query in self.search_queries['audits']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                if any(term in result['content'].lower() for term in ['audit', 'security', 'vulnerability']):
                    audits.append({
                        'source': result['url'],
                        'info': result['snippet'][:500]
                    })
        return audits
    
    async def _extract_partnerships(self, project_name: str) -> List[Dict[str, str]]:
        """Extract partnership information from search results."""
        partnerships = []
        for query in self.search_queries['partnerships']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                if any(term in result['content'].lower() for term in ['partner', 'collaborat', 'integrat']):
                    partnerships.append({
                        'source': result['url'],
                        'info': result['snippet'][:500]
                    })
        return partnerships
    
    async def _extract_controversies(self, project_name: str) -> List[Dict[str, str]]:
        """Extract controversy information from search results."""
        controversies = []
        for query in self.search_queries['controversies']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                if any(term in result['content'].lower() for term in ['controvers', 'issue', 'problem', 'critic']):
                    controversies.append({
                        'source': result['url'],
                        'info': result['snippet'][:500]
                    })
        return controversies
    
    async def _extract_rugpull_warnings(self, project_name: str) -> List[Dict[str, str]]:
        """Extract rugpull warnings from search results."""
        warnings = []
        for query in self.search_queries['rugpull_warnings']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                if any(term in result['content'].lower() for term in ['rug pull', 'scam', 'red flag', 'warning']):
                    warnings.append({
                        'source': result['url'],
                        'info': result['snippet'][:500]
                    })
        return warnings
    
    async def _analyze_social_activity(self, project_name: str) -> Dict[str, Any]:
        """Analyze social media activity for the project."""
        social_data = {
            'twitter': {'followers': None, 'activity': []},
            'telegram': {'members': None, 'activity': []},
            'discord': {'members': None, 'activity': []}
        }
        
        for query in self.search_queries['social_activity']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                content = result['content'].lower()
                if 'twitter' in content:
                    social_data['twitter']['activity'].append({
                        'source': result['url'],
                        'info': result['snippet'][:300]
                    })
                elif 'telegram' in content:
                    social_data['telegram']['activity'].append({
                        'source': result['url'],
                        'info': result['snippet'][:300]
                    })
                elif 'discord' in content:
                    social_data['discord']['activity'].append({
                        'source': result['url'],
                        'info': result['snippet'][:300]
                    })
        
        return social_data
    
    async def _analyze_roadmap(self, project_name: str) -> List[Dict[str, str]]:
        """Analyze project roadmap and progress."""
        roadmap_items = []
        for query in self.search_queries['roadmap']:
            results = await self._search_and_analyze(query.format(project=project_name))
            for result in results:
                if any(term in result['content'].lower() for term in ['roadmap', 'milestone', 'update', 'progress']):
                    roadmap_items.append({
                        'title': result['title'],
                        'source': result['url'],
                        'info': result['snippet'][:500]
                    })
        return roadmap_items
    
    async def research_project(self, project_name: str) -> ResearchFindings:
        """
        Perform comprehensive research on a crypto project.
        
        Args:
            project_name: Name or symbol of the crypto project to research
            
        Returns:
            ResearchFindings object containing all gathered information
        """
        print(f"🔍 Starting research on {project_name}...")
        
        # Gather all information in parallel
        team, audits, partnerships, controversies, rugpull_warnings, social_activity, roadmap = await asyncio.gather(
            self._extract_team_info(project_name),
            self._extract_audits(project_name),
            self._extract_partnerships(project_name),
            self._extract_controversies(project_name),
            self._extract_rugpull_warnings(project_name),
            self._analyze_social_activity(project_name),
            self._analyze_roadmap(project_name)
        )
        
        # Generate a summary
        summary = self._generate_summary(
            project_name, team, audits, partnerships, 
            controversies, rugpull_warnings, social_activity, roadmap
        )
        
        return ResearchFindings(
            project_name=project_name,
            team=team,
            audits=audits,
            partnerships=partnerships,
            controversies=controversies,
            rugpull_warnings=rugpull_warnings,
            social_activity=social_activity,
            roadmap=roadmap,
            summary=summary
        )
    
    def _generate_summary(
        self, 
        project_name: str,
        team: List[Dict[str, str]],
        audits: List[Dict[str, str]],
        partnerships: List[Dict[str, str]],
        controversies: List[Dict[str, str]],
        rugpull_warnings: List[Dict[str, str]],
        social_activity: Dict[str, Any],
        roadmap: Dict[str, str]
    ) -> str:
        """Generate a concise summary of the research findings."""
        summary_parts = [f"# {project_name} Research Summary\n"]
        
        # Team summary
        if team:
            summary_parts.append("## Team\n")
            summary_parts.append(f"- Found information about {len(team)} team members/roles.")
        
        # Audits summary
        if audits:
            summary_parts.append("\n## Security Audits\n")
            summary_parts.append(f"- Found {len(audits)} audit-related documents.")
        
        # Partnerships summary
        if partnerships:
            summary_parts.append("\n## Partnerships\n")
            summary_parts.append(f"- Found {len(partnerships)} potential partnerships or integrations.")
        
        # Controversies summary
        if controversies:
            summary_parts.append("\n## Controversies\n")
            summary_parts.append(f"- Found {len(controversies)} potential controversies or issues.")
        
        # Rugpull warnings summary
        if rugpull_warnings:
            summary_parts.append("\n## Risk Warnings\n")
            summary_parts.append(f"- Found {len(rugpull_warnings)} potential red flags or warnings.")
        
        # Social activity summary
        social_summary = []
        for platform, data in social_activity.items():
            if data['activity']:
                social_summary.append(f"- {platform.capitalize()}: Active")
        
        if social_summary:
            summary_parts.append("\n## Social Activity\n")
            summary_parts.extend(social_summary)
        
        # Roadmap summary
        if roadmap:
            summary_parts.append(f"\n## Roadmap\n")
            summary_parts.append(f"- Found {len(roadmap)} roadmap items or updates.")
        
        # Risk assessment
        risk_factors = sum([
            1 if controversies else 0,
            1 if rugpull_warnings else 0,
            0 if audits else 1,
            0 if team else 1
        ])
        
        risk_level = "Low"
        if risk_factors >= 3:
            risk_level = "High"
        elif risk_factors >= 1:
            risk_level = "Medium"
        
        summary_parts.append(f"\n## Risk Assessment: {risk_level}")
        
        return "\n".join(summary_parts)

# Example usage
async def example_usage():
    """Example of how to use the ResearchAgent."""
    from pprint import pprint
    
    # Initialize the agent
    agent = ResearchAgent()
    
    # Research a project
    project_name = "Ethereum"  # Example project
    findings = await agent.research_project(project_name)
    
    # Print the summary
    print("\n" + "="*80)
    print(findings.summary)
    print("\n" + "="*80)
    
    # Print detailed findings
    print("\nDetailed Findings:")
    print("-" * 40)
    
    print("\nTeam Members:")
    for i, member in enumerate(findings.team[:3], 1):
        print(f"{i}. {member['info'][:150]}...")
    
    if findings.audits:
        print("\nAudit Findings:")
        for i, audit in enumerate(findings.audits[:3], 1):
            print(f"{i}. {audit['info'][:150]}...")
    
    if findings.partnerships:
        print("\nPartnerships:")
        for i, partner in enumerate(findings.partnerships[:3], 1):
            print(f"{i}. {partner['info'][:150]}...")
    
    if findings.controversies:
        print("\nControversies:")
        for i, issue in enumerate(findings.controversies[:3], 1):
            print(f"{i}. {issue['info'][:150]}...")
    
    if findings.rugpull_warnings:
        print("\nRisk Warnings:")
        for i, warning in enumerate(findings.rugpull_warnings[:3], 1):
            print(f"{i}. {warning['info'][:150]}...")

if __name__ == "__main__":
    asyncio.run(example_usage())
