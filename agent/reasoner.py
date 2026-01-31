"""
Reasoner component - LLM-based reasoning about payment signals.

This is the agent's "thinking" layer. It interprets signals,
forms hypotheses, and reasons under uncertainty using an LLM.

IMPORTANT: This layer does NOT make decisions or take actions.
It only provides reasoning and interpretation.
"""

import logging
import json
import os
from typing import Dict, Any, Optional

import google.generativeai as genai

from agent.signals import PaymentSignals
from agent.reasoning_models import ReasoningResult


class Reasoner:
    """
    Reasons about payment events and failures using LLM.
    
    This component uses Gemini to understand complex patterns and uncertainties
    that are difficult to capture with rules.
    
    CRITICAL: This is pure cognition - no decisions, no actions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reasoner with Gemini API.
        
        Args:
            config: Configuration dictionary with:
                - gemini_api_key: Gemini API key (or from env)
                - gemini_model: Model name (default: gemini-2.0-flash-exp)
                - temperature: Sampling temperature (default: 0.3)
                - max_tokens: Max output tokens (default: 1000)
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Get API key
        api_key = self.config.get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.logger.warning("No Gemini API key found. Reasoning will use fallback mode.")
            self.llm_client = None
        else:
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Initialize model
            model_name = self.config.get('gemini_model', 'gemini-2.5-flash')
            self.llm_client = genai.GenerativeModel(model_name)
            
            self.logger.info(f"Initialized Gemini reasoner with model: {model_name}")
        
        # Generation config
        self.temperature = self.config.get('temperature', 0.3)
        self.max_tokens = self.config.get('max_tokens', 1000)
    
    async def reason(self, signals: PaymentSignals) -> ReasoningResult:
        """
        Reason about the payment signals.
        
        Args:
            signals: Aggregated payment signals from metrics engine
            
        Returns:
            Structured reasoning result with hypotheses and explanations
        """
        self.logger.info("Starting reasoning process")
        
        if self.llm_client is None:
            self.logger.warning("No LLM client available, using fallback reasoning")
            return self._fallback_reasoning(signals)
        
        try:
            # Build reasoning prompt
            prompt = self._build_reasoning_prompt(signals)
            
            # Call Gemini
            response = self.llm_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            # Parse response
            reasoning = self._parse_reasoning_response(response.text, signals)
            
            self.logger.info(f"Reasoning complete. Top hypothesis: {reasoning.get_top_hypothesis()}")
            
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Error during reasoning: {e}")
            return self._fallback_reasoning(signals)
    
    def _build_reasoning_prompt(self, signals: PaymentSignals) -> str:
        """
        Build prompt for LLM reasoning.
        
        Args:
            signals: Payment signals
            
        Returns:
            Formatted prompt
        """
        # Convert signals to readable format
        signals_summary = {
            "time_window": f"{signals.window_duration_seconds}s",
            "total_payments": signals.total_payments,
            "success_rate": f"{signals.overall_success_rate:.1%}",
            "failure_rate": f"{signals.overall_failure_rate:.1%}",
            "avg_latency_ms": f"{signals.avg_latency_ms:.0f}",
            "p95_latency_ms": f"{signals.p95_latency_ms:.0f}",
            "p99_latency_ms": f"{signals.p99_latency_ms:.0f}",
            "latency_trend": signals.latency_trend.value,
            "volume_trend": signals.volume_trend.value,
            "failure_rate_trend": signals.failure_rate_trend.value,
            "total_retries": signals.total_retries,
            "retry_effectiveness": f"{signals.retry_effectiveness:+.2f}",
            "degraded_banks": signals.degraded_banks,
            "degraded_methods": signals.degraded_methods,
            "top_errors": signals.top_errors[:5],
            "has_anomaly": signals.has_anomaly,
            "anomaly_severity": signals.anomaly_severity.value if signals.has_anomaly else "none"
        }
        
        # Add bank-specific details if there are issues
        if signals.degraded_banks:
            signals_summary["bank_failure_rates"] = {
                bank: f"{rate:.1%}"
                for bank, rate in signals.bank_failure_rates.items()
                if bank in signals.degraded_banks
            }
        
        # Add method-specific details if there are issues
        if signals.degraded_methods:
            signals_summary["method_failure_rates"] = {
                method: f"{rate:.1%}"
                for method, rate in signals.method_failure_rates.items()
                if method in signals.degraded_methods
            }
        
        prompt = f"""You are an expert payment systems analyst. Analyze the following payment system signals and provide structured reasoning.

PAYMENT SIGNALS:
{json.dumps(signals_summary, indent=2)}

YOUR TASK:
1. Identify possible root causes (hypotheses) with confidence scores (0.0 to 1.0)
2. Provide clear explanation of what you think is happening
3. State your assumptions
4. Identify what you're uncertain about
5. Give an overall confidence score

POSSIBLE HYPOTHESES (use these or create your own):
- bank_degradation: A specific bank is experiencing performance issues
- bank_outage: A bank is completely down
- network_issues: Network connectivity problems
- retry_storm: Excessive retries causing cascading failures
- fraud_spike: Unusual fraud detection activity
- rate_limiting: Rate limits being hit
- payment_method_issue: Specific payment method having problems
- normal_operation: Everything is operating normally
- peak_load: System under high load
- configuration_error: Misconfiguration causing issues

CRITICAL INSTRUCTIONS:
- Return ONLY valid JSON with no additional text or markdown
- Use double quotes for all strings
- Ensure all JSON is properly formatted
- Confidence scores must be numbers between 0.0 and 1.0

REQUIRED JSON SCHEMA:
{{
  "hypotheses": {{
    "hypothesis_name": 0.8,
    "another_hypothesis": 0.6
  }},
  "explanation": "Clear explanation of what is happening",
  "assumptions": ["assumption 1", "assumption 2"],
  "uncertainty": ["what you are unsure about"],
  "overall_confidence": 0.75
}}

Provide your reasoning as valid JSON:"""
        
        return prompt
    
    def _parse_reasoning_response(
        self,
        response_text: str,
        signals: PaymentSignals
    ) -> ReasoningResult:
        """
        Parse LLM response into structured reasoning.
        
        Args:
            response_text: Raw LLM response
            signals: Original signals (for fallback)
            
        Returns:
            Structured reasoning result
        """
        try:
            # Try to extract JSON from response
            # Sometimes LLM adds markdown code blocks
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            # Try to parse JSON
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                # Try to fix common JSON issues
                self.logger.warning(f"Initial JSON parse failed: {e}. Attempting to fix...")
                
                # Try to extract JSON object using regex
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    text = json_match.group(0)
                    # Try to fix common issues
                    text = text.replace("'", '"')  # Replace single quotes
                    text = re.sub(r',\s*}', '}', text)  # Remove trailing commas
                    text = re.sub(r',\s*]', ']', text)  # Remove trailing commas in arrays
                    parsed = json.loads(text)
                else:
                    raise
            
            # Validate and extract fields
            hypotheses = parsed.get("hypotheses", {})
            
            # Ensure confidence scores are valid
            hypotheses = {
                k: max(0.0, min(1.0, float(v)))
                for k, v in hypotheses.items()
            }
            
            reasoning = ReasoningResult(
                hypotheses=hypotheses,
                explanation=parsed.get("explanation", ""),
                assumptions=parsed.get("assumptions", []),
                uncertainty=parsed.get("uncertainty", []),
                overall_confidence=max(0.0, min(1.0, float(parsed.get("overall_confidence", 0.5)))),
                raw_response=response_text
            )
            
            return reasoning
            
        except Exception as e:
            self.logger.error(f"Failed to parse LLM response: {e}")
            self.logger.debug(f"Raw response: {response_text[:500]}")
            
            # Fallback to rule-based reasoning
            return self._fallback_reasoning(signals)
    
    def _fallback_reasoning(self, signals: PaymentSignals) -> ReasoningResult:
        """
        Fallback reasoning when LLM is unavailable or fails.
        
        This uses simple heuristics to provide basic reasoning.
        
        Args:
            signals: Payment signals
            
        Returns:
            Basic reasoning result
        """
        hypotheses = {}
        assumptions = []
        uncertainty = []
        explanation_parts = []
        
        # Check for normal operation
        if signals.overall_success_rate > 0.95 and not signals.has_anomaly:
            hypotheses["normal_operation"] = 0.9
            explanation_parts.append("System appears to be operating normally.")
        
        # Check for bank issues
        if signals.degraded_banks:
            hypotheses["bank_degradation"] = 0.8
            explanation_parts.append(
                f"Detected degraded banks: {', '.join(signals.degraded_banks)}."
            )
            assumptions.append("Bank degradation is the primary cause")
        
        # Check for high failure rate
        if signals.overall_failure_rate > 0.5:
            hypotheses["bank_outage"] = 0.7
            explanation_parts.append("Very high failure rate suggests possible outage.")
        
        # Check for latency issues
        if signals.p95_latency_ms > 1000:
            hypotheses["network_issues"] = 0.6
            explanation_parts.append("High latency detected.")
        
        # Check for retry storm
        if signals.total_retries > signals.total_payments * 0.3:
            hypotheses["retry_storm"] = 0.65
            explanation_parts.append("High retry rate detected.")
        
        # Check retry effectiveness
        if signals.retry_effectiveness < -0.2:
            uncertainty.append("Retries don't seem to be helping")
        
        # Default explanation
        if not explanation_parts:
            explanation_parts.append("Insufficient data for detailed analysis.")
            uncertainty.append("Limited signal data")
        
        # Calculate overall confidence
        if hypotheses:
            overall_confidence = max(hypotheses.values()) * 0.7  # Lower for fallback
        else:
            overall_confidence = 0.3
        
        return ReasoningResult(
            hypotheses=hypotheses,
            explanation=" ".join(explanation_parts),
            assumptions=assumptions,
            uncertainty=uncertainty,
            overall_confidence=overall_confidence,
            raw_response="[Fallback reasoning - no LLM]"
        )
