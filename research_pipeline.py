#!/usr/bin/env python3
"""
Research Pipeline for SpoonOS

This script demonstrates the complete research and analysis pipeline:
1. Research a project (startup, crypto, biotech, etc.) using ResearchAgent
2. Analyze the findings with multiple analyst agents
3. Present a consolidated report with detailed analysis
"""
import asyncio
import copy
import json
import argparse
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Import agents
from spoon_ai.agents.research_agent import ResearchAgent
from spoon_ai.agents.analyst_agents import (
    ConservativeAnalystAgent,
    ModerateAnalystAgent,
    AggressiveAnalystAgent,
    BaseAnalystAgent,
    AnalystRecommendation
)

# Reserved metadata bucket to avoid clobbering user-facing fields
RESEARCH_METADATA_KEY = "_research"
RESEARCH_PIPELINE_TAG = "research_pipeline_v1"
# Default test-mode toggle (used to keep behavior non-intrusive unless configured)
PIPELINE_TEST_MODE = os.getenv("RESEARCH_PIPELINE_TEST_MODE", "true").lower() == "true"

class ProjectType(str, Enum):
    """Supported project types for analysis."""
    CRYPTO = "crypto"
    TECH_STARTUP = "tech_startup"
    BIOTECH = "biotech"
    FINANCE = "finance"
    OTHER = "other"

@dataclass
class ResearchResult:
    """Container for research results."""
    project_name: str
    project_type: ProjectType
    summary: str
    raw_data: Dict[str, Any]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class TestResearchAgent:
    """Mock research agent for testing with predefined data."""
    
    def __init__(self, test_data: Dict[str, Any] = None):
        self.test_data = test_data or {}
    
    async def research_project(self, project_name: str, project_type: ProjectType = ProjectType.OTHER) -> ResearchResult:
        """Return predefined research data for testing."""
        if project_name in self.test_data:
            data = self.test_data[project_name]
            return ResearchResult(
                project_name=project_name,
                project_type=ProjectType(data.get('type', 'other')),
                summary=data.get('summary', ''),
                raw_data=data.get('data', {})
            )
        
        # Default test data if no match found
        return ResearchResult(
            project_name=project_name,
            project_type=project_type,
            summary=f"Research summary for {project_name}. This is a test response.",
            raw_data={"info": "Test data"}
        )

class ResearchPipeline:
    """Complete research and analysis pipeline for various project types."""
    
    def __init__(self, test_mode: bool = False, test_data: Optional[Dict] = None):
        """Initialize the pipeline with all required agents.
        
        Args:
            test_mode: If True, use test data instead of real research
            test_data: Optional predefined test data for research agent
        """
        self.test_mode = test_mode
        self.research_agent = TestResearchAgent(test_data) if test_mode else ResearchAgent()
        self.analysts = {
            'conservative': ConservativeAnalystAgent(),
            'moderate': ModerateAnalystAgent(),
            'aggressive': AggressiveAnalystAgent()
        }
    
    async def analyze_project(
        self, 
        project_name: str, 
        project_type: ProjectType = ProjectType.OTHER
    ) -> Dict:
        """
        Complete research and analysis of a project.
        
        Args:
            project_name: Name of the project to analyze
            project_type: Type of the project (crypto, biotech, etc.)
            
        Returns:
            Dictionary containing complete analysis results
        """
        print(f"🔍 Starting research on {project_name} ({project_type.value})...")
        
        # Step 1: Conduct research
        if not self.test_mode:
            print("\n🔄 Gathering project information...")
        research = await self.research_agent.research_project(project_name, project_type)
        
        # Step 2: Get analyses from all analysts
        if not self.test_mode:
            print("\n📊 Analyzing findings with different risk profiles...")
        analyses = {}
        for style, analyst in self.analysts.items():
            if not self.test_mode:
                print(f"   - {analyst.name} is reviewing...")
            analysis = analyst.analyze(research.summary)
            analyses[style] = analysis.dict()
        
        # Step 3: Generate final recommendation
        final_verdict = self._generate_final_verdict(analyses)
        
        # Prepare results
        result = {
            'project': project_name,
            'project_type': project_type.value,
            'timestamp': research.timestamp,
            'research_summary': research.summary,
            'raw_research': research.raw_data,
            'analyses': analyses,
            'final_verdict': final_verdict
        }
        
        # Add metadata
        result['metadata'] = {
            'test_mode': self.test_mode,
            'analyst_count': len(self.analysts),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
        return result
    
    def _generate_final_verdict(self, analyses: Dict) -> Dict:
        """Generate a final verdict based on all analyses."""
        # Count votes
        votes = sum(1 for a in analyses.values() if a['vote'])
        total = len(analyses)
        
        # Calculate average risk score
        avg_risk = sum(a['risk_score'] for a in analyses.values()) / total
        avg_confidence = sum(a['confidence'] for a in analyses.values()) / total
        
        # Determine overall recommendation
        recommendation = 'APPROVE' if votes > total / 2 else 'REJECT'
        
        return {
            'recommendation': recommendation,
            'approval_rate': f"{votes}/{total}",
            'average_risk_score': round(avg_risk, 1),
            'average_confidence': round(avg_confidence, 2)
        }
    
    @staticmethod
    def _format_timestamp(timestamp_str: str) -> str:
        """Format ISO timestamp to a more readable format."""
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

    @classmethod
    def print_report(cls, results: Dict):
        """Print a formatted report of the analysis with enhanced details."""
        print("\n" + "="*80)
        print(f"📈 FINAL RESEARCH REPORT: {results['project'].upper()}")
        print("="*80)
        
        # Print report metadata
        timestamp = cls._format_timestamp(results['timestamp'])
        print(f"\n📅 Report Generated: {timestamp}")
        
        # Enhanced research summary parsing
        print("\n🔍 DETAILED RESEARCH SUMMARY")
        print("-" * 80)
        
        # Parse and display the research summary with better formatting
        summary_lines = results['research_summary'].split('\n')
        current_section = None
        
        for line in summary_lines:
            line = line.strip()
            if not line:
                continue
                
            # Handle section headers
            if line.startswith('## '):
                current_section = line[3:].strip()
                print(f"\n{' ' + current_section.upper() + ' ':-^80}")
            # Handle sub-sections
            elif line.startswith('### '):
                print(f"\n{line[4:].upper()}")
                print("-" * len(line[4:]))
            # Handle list items
            elif line.startswith('- '):
                print(f"  • {line[2:]}")
            # Regular text
            else:
                # Simple word wrap for long lines
                import textwrap
                for wrapped_line in textwrap.wrap(line, width=78):
                    print(f"  {wrapped_line}")
        
        # Print analyst reports with enhanced formatting
        print("\n📊 ANALYST RECOMMENDATIONS")
        print("-" * 80)
        
        for style, analysis in results['analyses'].items():
            print(f"\n{' ' + style.upper() + ' ANALYST ':-^80}")
            print(f"🔍 Risk Assessment: {analysis['risk_score']:.1f}/10")
            print(f"📊 Verdict: {'✅ APPROVE' if analysis['vote'] else '❌ REJECT'}")
            print(f"💎 Confidence: {analysis['confidence']*100:.0f}%")
            
            # Format justification with better readability
            print("\n📝 Detailed Analysis:")
            for part in analysis['justification'].split('\n'):
                if part.strip() == '':
                    continue
                if part.endswith(':'):
                    print(f"\n{part}")
                elif part.startswith('✅') or part.startswith('⚠️') or part.startswith('❌'):
                    print(f"\n{part}")
                elif part.startswith('-'):
                    print(f"  • {part[1:].strip()}")
                else:
                    print(f"  {part}")
        
        # Enhanced final verdict
        verdict = results['final_verdict']
        print("\n🎯 FINAL VERDICT")
        print("-" * 80)
        
        if verdict['recommendation'] == 'APPROVE':
            print("✅ RECOMMENDATION: APPROVE")
            print("   This project meets the criteria for consideration based on the analysis.")
        else:
            print("❌ RECOMMENDATION: REJECT")
            print("   This project does not meet the minimum criteria for approval.")
            
        print(f"\n📊 Consensus: {verdict['approval_rate']} analysts in favor")
        print(f"📈 Average Risk Score: {verdict['average_risk_score']}/10")
        print(f"💎 Average Confidence: {verdict['average_confidence']*100:.0f}%")
        
        # Additional context based on risk level
        avg_risk = float(verdict['average_risk_score'])
        if avg_risk < 3:
            print("\n💡 This project is considered low risk with strong fundamentals.")
        elif avg_risk < 7:
            print("\n⚠️  This project carries moderate risk. Please review the analysis carefully.")
        else:
            print("\n🚨 This project is considered high risk. Exercise extreme caution and conduct additional due diligence.")
            
        print("\n" + "="*80 + "\n")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Research and analyze projects.')
    parser.add_argument('project', nargs='?', default=None, 
                       help='Name of the project to analyze')
    parser.add_argument('--type', type=str, default='other',
                       choices=[t.value for t in ProjectType],
                       help='Type of project')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode with sample data')
    parser.add_argument('--list-tests', action='store_true',
                       help='List available test cases')
    parser.add_argument('--run-all-tests', action='store_true',
                       help='Run all test cases')
    return parser.parse_args()

# Sample test data for different project types
SAMPLE_TEST_DATA = {
    "CloudScale AI": {
        "type": "tech_startup",
        "summary": """
Project: CloudScale AI

Team: Led by former Google Cloud engineers with 10+ years of experience in distributed systems and AI.
Strong technical leadership with proven track record in scaling cloud infrastructure.

Market: Targeting the $500B cloud computing market with a focus on AI/ML workloads.
Growing demand for specialized AI infrastructure solutions.

Financials: $20M in Series A funding from top-tier VCs. Projected 5x revenue growth in next 2 years.
Current burn rate allows for 24 months of runway.

Risks: Facing competition from established cloud providers. Reliant on continued AI/ML adoption growth.
Regulatory scrutiny of AI technologies could impact market.

Partnerships: Strategic partnerships with NVIDIA and Databricks. Pilot program with Fortune 500 companies.

Differentiation: Proprietary auto-scaling technology reduces AI training costs by 60% compared to competitors.
"""
    },
    "GeneCure Therapeutics": {
        "type": "biotech",
        "summary": """
Project: GeneCure Therapeutics

Team: World-class scientists with PhDs from top institutions. Strong advisory board including
Nobel laureate Dr. Sarah Chen. Experienced management team from leading pharma companies.

Product: Breakthrough gene therapy for rare genetic disorder affecting 1 in 50,000 people.
Orphan drug designation granted in US and EU. Phase 2 clinical trials show 85% efficacy.

Market: $3B+ addressable market with no direct competitors. Strong pricing power with potential
$500K-$1M per treatment. Fast-track FDA designation expected.

Risks: Clinical trial risks remain. Manufacturing scale-up challenges. Reimbursement hurdles.
Regulatory approval not guaranteed despite promising early results.

Financials: $150M in funding. Cash runway through Phase 3 trials. Multiple big pharma
partnership discussions in progress.
"""
    },
    "Nexus Protocol": {
        "type": "crypto",
        "summary": """
Project: Nexus Protocol

Team: Anonymous team with strong technical documentation. Core contributors have verifiable
experience in DeFi protocols. Active development with regular code commits and updates.

Technology: Layer 2 scaling solution for Ethereum with zero-knowledge proofs. 10,000+ TPS capacity.
Fully open-source with comprehensive documentation.

Ecosystem: $50M developer grant program. 100+ projects building on testnet. Strategic
partnerships with major DeFi protocols. Backed by leading crypto VCs.

Risks: Smart contract risks despite audits. Regulatory uncertainty in key markets.
Dependent on Ethereum's roadmap and adoption. Strong competition from other L2 solutions.

Tokenomics: 1B total supply. 40% community incentives, 25% team (4-year vesting), 20% investors,
15% ecosystem fund. Inflationary rewards with halving every 4 years.
"""
    }
}

async def run_analysis(project_name: str, project_type: ProjectType, test_mode: bool = False, test_data: Optional[Dict] = None):
    """Run the analysis pipeline for a single project."""
    pipeline = ResearchPipeline(test_mode=test_mode, test_data=test_data)
    results = await pipeline.analyze_project(project_name, project_type)
    
    # Print and save results
    pipeline.print_report(results)
    
    # Save full results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"research_{project_name.lower().replace(' ', '_')}_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Full report saved to: {filename}")
    return results

async def run_all_tests():
    """Run all test cases."""
    print("🚀 Running all test cases...\n")
    results = []
    
    for project_name, data in SAMPLE_TEST_DATA.items():
        print(f"\n{'='*80}")
        print(f"🧪 TESTING: {project_name}")
        print(f"{'='*80}")
        
        result = await run_analysis(
            project_name=project_name,
            project_type=ProjectType(data['type']),
            test_mode=True,
            test_data=SAMPLE_TEST_DATA
        )
        results.append(result)
        
        # Add spacing between tests
        if project_name != list(SAMPLE_TEST_DATA.keys())[-1]:
            print("\n" + "="*120 + "\n")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    for result in results:
        verdict = result['final_verdict']
        print(f"\n📌 {result['project']} ({result['project_type']})")
        print(f"   Verdict: {'✅ APPROVED' if verdict['recommendation'] == 'APPROVE' else '❌ REJECTED'}")
        print(f"   Approval: {verdict['approval_rate']} analysts")
        print(f"   Avg Risk: {verdict['average_risk_score']}/10")
        print(f"   Confidence: {verdict['average_confidence']*100:.0f}%")
    
    return results


def process_proposal(proposal: Dict[str, Any], test_mode: Optional[bool] = None) -> Dict[str, Any]:
    """
    Public, idempotent hook to run a proposal through the research pipeline.

    Args:
        proposal: Proposal payload (expects 'title' and metadata dict)
        test_mode: Optional override for pipeline test mode (defaults to env)

    Returns:
        Proposal dict with research results attached under reserved metadata key.
        On failure, returns the original proposal unchanged (fail-open).
    """
    if not isinstance(proposal, dict):
        return proposal

    proposal_copy = copy.deepcopy(proposal)
    metadata_key = (
        "metadata"
        if "metadata" in proposal_copy
        else "proposal_metadata"
        if "proposal_metadata" in proposal_copy
        else "metadata"
    )
    metadata = copy.deepcopy(proposal_copy.get(metadata_key) or {})

    existing_research = metadata.get(RESEARCH_METADATA_KEY, {})
    if isinstance(existing_research, dict) and existing_research.get("tag") == RESEARCH_PIPELINE_TAG:
        proposal_copy[metadata_key] = metadata
        return proposal_copy

    resolved_test_mode = PIPELINE_TEST_MODE if test_mode is None else bool(test_mode)

    project_name = proposal_copy.get("title") or metadata.get("startup_name") or "Unknown Project"
    project_type_str = metadata.get("project_type") or metadata.get("sector") or ProjectType.TECH_STARTUP.value
    project_type = (
        ProjectType(project_type_str)
        if project_type_str in ProjectType._value2member_map_
        else ProjectType.TECH_STARTUP
    )

    pipeline = ResearchPipeline(test_mode=resolved_test_mode)

    def _run_pipeline() -> Dict[str, Any]:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(pipeline.analyze_project(project_name, project_type))
        finally:
            loop.close()

    try:
        analysis = _run_pipeline()
    except Exception as exc:
        # Fail-open: preserve original proposal and record error under reserved metadata
        metadata.setdefault(RESEARCH_METADATA_KEY, {})
        if isinstance(metadata[RESEARCH_METADATA_KEY], dict):
            errors = metadata[RESEARCH_METADATA_KEY].get("errors", [])
            errors.append(str(exc))
            metadata[RESEARCH_METADATA_KEY]["errors"] = errors
        proposal_copy[metadata_key] = metadata
        return proposal_copy

    metadata.setdefault(RESEARCH_METADATA_KEY, {})
    if isinstance(metadata[RESEARCH_METADATA_KEY], dict):
        metadata[RESEARCH_METADATA_KEY].update(
            {
                "tag": RESEARCH_PIPELINE_TAG,
                "analysis": analysis,
                "updated_at": datetime.utcnow().isoformat(),
                "test_mode": resolved_test_mode,
            }
        )
    proposal_copy[metadata_key] = metadata
    return proposal_copy

async def main():
    """Main entry point for the research pipeline."""
    args = parse_arguments()
    
    if args.list_tests:
        print("\nAvailable test cases:")
        for i, name in enumerate(SAMPLE_TEST_DATA.keys(), 1):
            print(f"  {i}. {name} ({SAMPLE_TEST_DATA[name]['type']})")
        return
    
    if args.run_all_tests:
        await run_all_tests()
        return
    
    # Default to running a single analysis
    project_name = args.project or "Example Project"
    project_type = ProjectType(args.type)
    
    if args.test:
        await run_analysis(
            project_name=project_name,
            project_type=project_type,
            test_mode=True,
            test_data=SAMPLE_TEST_DATA
        )
    else:
        await run_analysis(
            project_name=project_name,
            project_type=project_type,
            test_mode=False
        )

if __name__ == "__main__":
    asyncio.run(main())
