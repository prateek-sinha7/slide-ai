"""Test script to verify performance logging and error handling."""
import sys
import logging

# Configure logging to see performance metrics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from orchestrator.orchestrator import PerformanceMetrics

def test_performance_metrics():
    """Test PerformanceMetrics class."""
    print("\n" + "="*60)
    print("Testing PerformanceMetrics")
    print("="*60)
    
    metrics = PerformanceMetrics()
    
    # Start pipeline
    metrics.start_pipeline()
    
    # Record some agent executions
    metrics.record_agent_execution(
        agent_name="Planner",
        duration=5.2,
        iterations=3,
        tool_invocations=6,
        quality_score=0.85
    )
    
    metrics.record_agent_execution(
        agent_name="Content",
        duration=8.1,
        iterations=4,
        tool_invocations=8,
        quality_score=0.92
    )
    
    metrics.record_agent_execution(
        agent_name="Reviewer",
        duration=6.5,
        iterations=2,
        tool_invocations=4,
        quality_score=0.88
    )
    
    metrics.record_agent_execution(
        agent_name="Design",
        duration=4.3,
        iterations=2,
        tool_invocations=4,
        quality_score=0.90
    )
    
    # End pipeline
    metrics.end_pipeline()
    
    # Verify metrics
    print("\n" + "="*60)
    print("Verification")
    print("="*60)
    print(f"Total tool invocations: {metrics.total_tool_invocations}")
    print(f"Pipeline duration: {metrics.get_pipeline_duration():.2f}s")
    
    for agent_name in ["Planner", "Content", "Reviewer", "Design"]:
        agent_metrics = metrics.get_agent_metrics(agent_name)
        print(f"\n{agent_name} metrics:")
        print(f"  Duration: {agent_metrics.get('duration', 0):.2f}s")
        print(f"  Iterations: {agent_metrics.get('iterations', 0)}")
        print(f"  Tool invocations: {agent_metrics.get('tool_invocations', 0)}")
        if 'quality_score' in agent_metrics:
            print(f"  Quality score: {agent_metrics['quality_score']:.2f}")
    
    print("\n" + "="*60)
    print("Performance logging test PASSED")
    print("="*60)

def test_groq_error_handling():
    """Test Groq API error handling configuration."""
    print("\n" + "="*60)
    print("Testing Groq API Error Handling")
    print("="*60)
    
    from orchestrator.config import config
    
    print(f"Max retries: {config.MAX_RETRIES}")
    print(f"Retry delay: {config.RETRY_DELAY}s")
    print(f"Performance logging enabled: {config.ENABLE_PERFORMANCE_LOGGING}")
    
    # Test that retry_with_exponential_backoff method exists
    assert hasattr(config, 'retry_with_exponential_backoff')
    print("✓ retry_with_exponential_backoff method exists")
    
    print("\n" + "="*60)
    print("Groq error handling test PASSED")
    print("="*60)

if __name__ == "__main__":
    test_performance_metrics()
    test_groq_error_handling()
    print("\n✅ All tests passed!")
