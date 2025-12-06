"""
Analyst Agents for SpoonOS

This module contains different analyst agents with varying risk tolerance levels
that can analyze any project research and provide investment recommendations.
"""
from typing import Dict, Any, Tuple, List
from pydantic import BaseModel, Field, validator
import random

class AnalystRecommendation(BaseModel):
    """Structured output from an analyst agent."""
    project_name: str = Field(..., description="Name of the project being analyzed")
    risk_score: float = Field(..., ge=0, le=10, description="Risk score from 0 (safest) to 10 (riskiest)")
    vote: bool = Field(..., description="Recommendation: True for YES/Invest, False for NO/Pass")
    justification: str = Field(..., description="Detailed explanation of the recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level from 0 to 1")
    strengths: List[str] = Field(default_factory=list, description="List of key strengths")
    weaknesses: List[str] = Field(default_factory=list, description="List of key weaknesses")

class BaseAnalystAgent:
    """Base class for analyst agents with common functionality."""
    
    def __init__(self, name: str, risk_bias: float):
        """
        Initialize the analyst agent.
        
        Args:
            name: Name of the analyst
            risk_bias: Bias factor for risk scoring (0.5-1.5)
        """
        self.name = name
        self.risk_bias = risk_bias
    
    def _extract_project_name(self, research_summary: str) -> str:
        """Extract project name from research summary."""
        # Look for project name in common patterns
        for line in research_summary.split('\n'):
            if line.lower().startswith(('project:', 'company:', 'startup:')):
                return line.split(':', 1)[1].strip()
        return "Project"

    def _calculate_risk_score(self, research_summary: str) -> Tuple[float, List[str], List[str]]:
        """
        Calculate base risk score from research summary (0-10 scale).
        
        Returns:
            Tuple of (risk_score, strengths, weaknesses)
        """
        # Initialize risk score and analysis components
        risk_score = 5.0  # Start with neutral score
        strengths = []
        weaknesses = []
        
        # Positive indicators (reduce risk)
        positive_indicators = [
            ("strong team", -1.5, "Strong team with relevant experience"),
            ("proven track record", -1.2, "Established track record of success"),
            ("growing market", -1.0, "Addressing a growing market"),
            ("revenue", -0.8, "Existing revenue streams"),
            ("partnership", -0.7, "Strategic partnerships"),
            ("funding", -0.6, "Adequate funding"),
            ("competitive advantage", -0.8, "Clear competitive advantage"),
        ]
        
        # Risk indicators (increase risk)
        risk_indicators = [
            # Business/Operational Risks
            ("high competition", 1.0, "Faces significant competition"),
            ("regulatory risk", 1.5, "Potential regulatory challenges"),
            ("cash burn", 1.2, "High cash burn rate"),
            ("dependenc", 0.8, "Dependent on third parties"),
            
            # Team/Leadership Risks
            ("inexperienced team", 1.0, "Lack of relevant experience"),
            ("team conflict", 1.5, "Potential team conflicts"),
            ("key person risk", 1.2, "Reliance on key individuals"),
            
            # Market Risks
            ("saturated market", 0.8, "Competing in a saturated market"),
            ("economic downturn", 0.7, "Vulnerable to economic downturns"),
            ("market risk", 0.7, "General market risks present"),
            
            # Technology/Product Risks
            ("unproven technology", 1.0, "Relies on unproven technology"),
            ("scalability issues", 1.2, "Potential scalability challenges"),
            ("security concern", 1.5, "Security concerns identified"),
            ("product-market fit", 1.0, "Unclear product-market fit"),
        ]
        
        # Convert to lowercase for case-insensitive matching
        research_lower = research_summary.lower()
        
        # Check for positive indicators
        for term, impact, description in positive_indicators:
            if term in research_lower:
                risk_score = max(0, risk_score + impact)
                if description not in strengths:
                    strengths.append(description)
        
        # Check for risk indicators
        for term, impact, description in risk_indicators:
            if term in research_lower:
                risk_score = min(10, risk_score + impact)
                if description not in weaknesses:
                    weaknesses.append(description)
        
        # Add generic strengths/weaknesses if none found
        if not strengths and not weaknesses:
            if risk_score < 4:
                strengths.append("Multiple positive indicators found")
            elif risk_score > 6:
                weaknesses.append("Several risk factors identified")
        
        # Ensure score is within bounds
        risk_score = max(0, min(10, risk_score))
        
        return risk_score, strengths, weaknesses
        
    def _format_analysis(self, risk_score: float, strengths: List[str], weaknesses: List[str]) -> str:
        """Format the analysis with bullet points."""
        analysis = []
        
        # Add strengths if any
        if strengths:
            analysis.append("✅ **Strengths:**")
            analysis.extend(f"  • {s}" for s in strengths)
            
        # Add weaknesses if any
        if weaknesses:
            if analysis:  # Add a newline if we already have content
                analysis.append("")
            analysis.append("⚠️ **Risks & Concerns:**")
            analysis.extend(f"  • {w}" for w in weaknesses)
            
        return "\n".join(analysis)
        
    def _determine_confidence(self, research_summary: str) -> float:
        """Determine confidence level based on research quality."""
        # More comprehensive research increases confidence
        word_count = len(research_summary.split())
        confidence = min(1.0, word_count / 500)  # Cap at 1.0 (100%)
        
        # Adjust based on presence of key sections
        key_sections = ["team", "market", "financial", "competition", "risks"]
        section_count = sum(1 for section in key_sections if section in research_summary.lower())
        confidence = min(1.0, confidence + (section_count * 0.1))  # 10% per key section
        
        return max(0.1, min(1.0, confidence))  # Keep between 10% and 100%
        
    def analyze(self, research_summary: str) -> AnalystRecommendation:
        """
        Analyze research and provide a recommendation with detailed reasoning.
        
        Args:
            research_summary: Summary of research findings
            
        Returns:
            AnalystRecommendation with risk score, vote, and detailed justification
        """
        # Extract project name
        project_name = self._extract_project_name(research_summary)
        
        # Calculate risk score and get analysis components
        risk_score, strengths, weaknesses = self._calculate_risk_score(research_summary)
        
        # Determine vote based on risk score and agent's risk tolerance
        vote = risk_score < (7.0 if isinstance(self, ConservativeAnalystAgent) else 
                            (6.5 if isinstance(self, ModerateAnalystAgent) else 6.0))
        confidence = 0.7 + (random.random() * 0.3)  # 0.7-1.0 confidence
        
        # Generate formatted analysis
        analysis = self._format_analysis(risk_score, strengths, weaknesses)
        
        # Generate justification
        justification = (
            f"# {project_name} - Investment Analysis\n\n"
            f"**Risk Score:** {risk_score:.1f}/10\n"
            f"**Recommendation:** {'✅ APPROVE' if vote else '❌ REJECT'}\n\n"
            f"## Analysis Summary\n{analysis}\n\n"
            f"## Final Verdict\n"
        )
        
        if vote:
            justification += (
                f"Despite the risks, {project_name} shows strong fundamentals that align with our investment criteria. "
                "The project demonstrates a solid foundation with multiple positive indicators that outweigh the identified risks."
            )
        else:
            justification += (
                f"After careful consideration, we cannot recommend investing in {project_name} at this time. "
                "The project presents several risk factors that exceed our risk tolerance thresholds."
            )
        
        # Confidence based on research quality
        confidence = self._determine_confidence(research_summary)
        
        return AnalystRecommendation(
            project_name=project_name,
            risk_score=risk_score,
            vote=vote,
            justification=justification,
            confidence=confidence,
            strengths=strengths,
            weaknesses=weaknesses
        )


class ConservativeAnalystAgent(BaseAnalystAgent):
    """Analyst with conservative risk tolerance."""
    
    def __init__(self):
        super().__init__(
            name="Conservative Analyst",
            risk_bias=1.3  # Higher weight on risks
        )
        
    def analyze(self, research_summary: str) -> AnalystRecommendation:
        """
        Analyze research with a conservative approach.
        
        Args:
            research_summary: Summary of research findings
            
        Returns:
            AnalystRecommendation with conservative analysis
        """
        # Extract project name
        project_name = self._extract_project_name(research_summary)
        
        # Calculate risk score and get analysis components
        risk_score, strengths, weaknesses = self._calculate_risk_score(research_summary)
        
        # Conservative approach: higher threshold for approval
        # and higher weight on risks
        adjusted_score = risk_score * self.risk_bias
        
        # Determine vote based on adjusted score
        vote = adjusted_score < 3.0  # Only invest if very low risk
        
        # Generate formatted analysis
        analysis = self._format_analysis(risk_score, strengths, weaknesses)
        
        # Generate justification
        justification = (
            f"# {project_name} - Conservative Investment Analysis\n\n"
            f"**Risk Score:** {risk_score:.1f}/10\n"
            f"**Adjusted Score:** {adjusted_score:.1f}/10 (with conservative bias)\n"
            f"**Recommendation:** {'✅ APPROVE' if vote else '❌ REJECT'}\n\n"
            f"## Analysis Summary\n{analysis}\n\n"
            f"## Final Verdict\n"
        )
        
        if vote:
            justification += (
                f"Despite the risks, {project_name} shows exceptionally strong fundamentals that align with our conservative investment criteria. "
                "The project demonstrates a solid foundation with multiple positive indicators that significantly outweigh the identified risks."
            )
        else:
            justification += (
                f"After careful consideration, we cannot recommend investing in {project_name} at this time. "
                "The project presents several risk factors that exceed our conservative risk tolerance thresholds. "
                f"The adjusted risk score of {adjusted_score:.1f} is above our conservative threshold of 3.0."
            )
        
        # Confidence based on research quality
        confidence = self._determine_confidence(research_summary)
        
        return AnalystRecommendation(
            project_name=project_name,
            risk_score=risk_score,
            vote=vote,
            justification=justification,
            confidence=confidence,
            strengths=strengths,
            weaknesses=weaknesses
        )
        # Build detailed justification
        justification = []
        if positive_factors:
            justification.append("✅ Positive aspects:")
            justification.extend([f"  • {factor}" for factor in positive_factors])
            
        if negative_factors:
            if positive_factors:
                justification.append("")  # Add spacing
            justification.append("❌ Negative aspects:")
            justification.extend([f"  • {factor}" for factor in negative_factors])
        
        # Add risk assessment
        justification.append("\n📊 Final Assessment:")
        if risk_score >= 8:
            justification.append("🚨 CRITICAL RISK: Multiple severe concerns identified that make this a highly risky investment.")
        elif risk_score >= 6:
            justification.append("⚠️  HIGH RISK: Significant concerns exist that require careful consideration.")
        elif risk_score >= 4:
            justification.append("⚠️  MODERATE RISK: Some concerns present but may be acceptable depending on risk tolerance.")
            conclusion = "\n✅ Very low risk profile. The project demonstrates strong fundamentals and robust security measures that align with conservative investment criteria."
        elif risk_score < 4:
            justification.append("⚠️  MODERATE RISK: Some concerns present but may be acceptable depending on risk tolerance.")
        else:
            justification.append("❌ HIGH RISK: Multiple concerning factors have been identified that do not meet the stringent requirements for conservative investment consideration.")
            
        justification.append(f"\n💡 Recommendation: {'✅ APPROVE' if vote else '❌ REJECT'}")
        justification.append(f"📊 Risk Score: {risk_score}/10")
        justification.append(f"💎 Confidence: {confidence*100:.0f}%")
        
        return AnalystRecommendation(
            risk_score=round(risk_score, 1),
            vote=vote,
            justification='\n'.join(justification),
            confidence=round(confidence, 2)
        )


class ModerateAnalystAgent(BaseAnalystAgent):
    """Analyst with moderate risk tolerance."""
    
    def __init__(self):
        super().__init__(
            name="Moderate Analyst",
            risk_bias=1.0  # Neutral risk weighting
        )
    
    def analyze(self, research_summary: str) -> AnalystRecommendation:
        # Unpack the tuple returned by _calculate_risk_score
        risk_score, strengths, weaknesses = self._calculate_risk_score(research_summary)
        
        # Extract key information from research
        risk_factors = []
        positive_factors = []
        
        # Check for specific risk factors
        if any(term in research_summary.lower() for term in ["unaudited", "no audit"]):
            risk_factors.append("Project has not undergone a security audit")
        if any(term in research_summary.lower() for term in ["anonymous team", "team unknown"]):
            risk_factors.append("Development team is anonymous")
        if "centralized" in research_summary.lower():
            risk_factors.append("Project shows signs of centralization")
            
        # Check for positive factors
        if any(term in research_summary.lower() for term in ["audited by", "security audit"]):
            positive_factors.append("Project has completed security audits")
        if any(term in research_summary.lower() for term in ["doxxed team", "public team"]):
            positive_factors.append("Development team is public and verifiable")
        if "partnership" in research_summary.lower():
            positive_factors.append("Established partnerships with reputable organizations")
        
        # Add any additional strengths/weaknesses from the base analysis
        strengths.extend(positive_factors)
        weaknesses.extend(risk_factors)
        
        # Moderate: Middle ground for recommendations
        vote = risk_score < 5.0
        
        # Generate detailed justification
        justification_parts = []
        
        if risk_factors:
            justification_parts.append("Risk assessment identified:")
            justification_parts.extend([f"- {factor}" for factor in risk_factors])
        
        if positive_factors:
            justification_parts.append("\nPositive indicators:")
            justification_parts.extend([f"- {factor}" for factor in positive_factors])
        
        if risk_score < 3:
            conclusion = "\n✅ Low risk. The project demonstrates strong fundamentals and an acceptable risk profile that aligns with moderate investment strategies."
        elif risk_score < 6:
            conclusion = "\n⚠️ Moderate risk. While there are some concerns, the potential upside may justify the calculated risk for investors with balanced risk tolerance."
        else:
            conclusion = "\n❌ High risk. The identified concerns are significant and may outweigh the potential rewards, suggesting caution is warranted."
        
        justification_parts.append(conclusion)
        
        # Confidence based on risk score and information quality
        confidence = 0.65 + (0.3 * (1 - (risk_score / 10)))  # Higher confidence for lower risk
        confidence = min(0.9, max(0.6, confidence))  # Keep within 0.6-0.9 range
        
        return AnalystRecommendation(
            project_name=self._extract_project_name(research_summary),
            risk_score=round(risk_score, 1),
            vote=vote,
            justification='\n'.join(justification_parts),
            confidence=round(confidence, 2),
            strengths=strengths,
            weaknesses=weaknesses
        )


class AggressiveAnalystAgent(BaseAnalystAgent):
    """Analyst with aggressive risk tolerance."""
    
    def __init__(self):
        super().__init__(
            name="Aggressive Analyst",
            risk_bias=0.7  # Lower weight on risks
        )
    
    def analyze(self, research_summary: str) -> AnalystRecommendation:
        # Unpack the tuple returned by _calculate_risk_score
        risk_score, strengths, weaknesses = self._calculate_risk_score(research_summary)
        
        # Extract key information from research
        risk_factors = []
        positive_factors = []
        
        # Check for specific risk factors
        if any(term in research_summary.lower() for term in ["unaudited", "no audit"]):
            risk_factors.append("Project has not undergone a security audit")
        if any(term in research_summary.lower() for term in ["anonymous team", "team unknown"]):
            risk_factors.append("Development team is anonymous")
        if "centralized" in research_summary.lower():
            risk_factors.append("Project shows signs of centralization")
            
        # Check for positive factors
        if any(term in research_summary.lower() for term in ["audited by", "security audit"]):
            positive_factors.append("Project has completed security audits")
        if any(term in research_summary.lower() for term in ["doxxed team", "public team"]):
            positive_factors.append("Development team is public and verifiable")
        if "partnership" in research_summary.lower():
            positive_factors.append("Established partnerships with reputable organizations")
        
        # Add any additional strengths/weaknesses from the base analysis
        strengths.extend(positive_factors)
        weaknesses.extend(risk_factors)
        
        # Aggressive: Willing to take on more risk
        vote = risk_score < 7.0
        
        # Generate detailed justification
        justification_parts = []
        
        if risk_factors:
            justification_parts.append("Notable risk factors:")
            justification_parts.extend([f"- {factor}" for factor in risk_factors])
        
        if positive_factors:
            justification_parts.append("\nKey strengths:")
            justification_parts.extend([f"- {factor}" for factor in positive_factors])
        
        if risk_score < 4:
            conclusion = "\n✅ Low risk. The project shows strong potential with minimal concerns, making it a compelling opportunity for aggressive investors."
        elif risk_score < 7:
            conclusion = "\n⚠️ Moderate risk. While risks are present, the potential rewards appear to justify the investment for those with higher risk tolerance."
        else:
            conclusion = "\n⚠️ High risk. Significant concerns exist, but the potential for outsized returns may appeal to the most risk-tolerant investors."
        
        justification_parts.append(conclusion)
        
        # Confidence calculation - aggressive investors are more confident in their risk tolerance
        confidence = 0.7 + (0.3 * (1 - (risk_score / 15)))  # More forgiving curve for aggressive investors
        confidence = min(0.9, max(0.5, confidence))  # Keep within 0.5-0.9 range
        
        return AnalystRecommendation(
            project_name=self._extract_project_name(research_summary),
            risk_score=round(risk_score, 1),
            vote=vote,
            justification='\n'.join(justification_parts),
            confidence=round(confidence, 2),
            strengths=strengths,
            weaknesses=weaknesses
        )


def get_analyst_agent(style: str) -> BaseAnalystAgent:
    """Factory function to get an analyst agent by style."""
    style = style.lower()
    if style == 'conservative':
        return ConservativeAnalystAgent()
    elif style == 'moderate':
        return ModerateAnalystAgent()
    elif style == 'aggressive':
        return AggressiveAnalystAgent()
    else:
        raise ValueError(f"Unknown analyst style: {style}")
