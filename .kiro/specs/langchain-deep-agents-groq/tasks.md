# Implementation Plan: LangChain Deep Agents with Groq API

## Overview

This implementation plan transforms the current simple prompt-response chains into true LangChain agents using the ReAct (Reasoning + Acting) pattern. The system will add Groq API support alongside existing LLM providers (Ollama, OpenAI, Anthropic) while implementing autonomous agents with tool usage, reasoning loops, and memory systems.

**Key Changes:**
- Add Groq API support (keep Ollama, OpenAI, Anthropic options)
- Implement ReAct agents with AgentExecutor for all four agents
- Create 12+ specialized tools for agent use
- Add conversation memory and intermediate result caching
- Implement quality-based iteration with 3-5 max iterations
- Maintain backward compatibility with existing API

## Tasks

- [ ] 1. Add Groq API support alongside existing LLM providers
  - Install langchain-groq package in requirements.txt
  - Update backend/orchestrator/config.py to support groq provider (keep ollama, openai, anthropic)
  - Add GROQ_API_KEY configuration with provided key
  - Add Groq model selection (llama-3.1-70b-versatile, mixtral-8x7b-32768)
  - Add max_iterations configuration (default: 5)
  - Add quality_threshold configuration for early stopping
  - Keep all existing Ollama, OpenAI, and Anthropic configurations
  - Update .env.example to show all provider options
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 2. Create shared tool infrastructure
  - [ ] 2.1 Create backend/orchestrator/tools/ directory structure
    - Create __init__.py for tools module
    - Create base_tool.py with BaseTool abstract class
    - Create tool_registry.py for centralized tool management
    - _Requirements: 2.3, 14.2_
  
  - [ ] 2.2 Implement memory system infrastructure
    - Create backend/orchestrator/memory.py
    - Implement ConversationMemory class using LangChain's ConversationBufferMemory
    - Implement IntermediateResultsCache class for cross-agent sharing
    - Add memory persistence throughout pipeline execution
    - Add cache clear functionality
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 14.5_

- [ ] 3. Implement Planner Agent tools
  - [ ] 3.1 Create web search tool for Planner Agent
    - Create backend/orchestrator/tools/planner_tools.py
    - Implement WebSearchTool using DuckDuckGo or Tavily API
    - Add error handling for search failures
    - _Requirements: 3.1, 3.4, 12.1, 12.4_
  
  - [ ] 3.2 Create content structure validator tool
    - Implement StructureValidatorTool in planner_tools.py
    - Validate logical flow and coherent narrative
    - Return validation score (0-100) and feedback
    - _Requirements: 3.2, 3.5_
  
  - [ ] 3.3 Create outline quality checker tool
    - Implement OutlineQualityCheckerTool in planner_tools.py
    - Score outline against presentation best practices
    - Check title clarity, flow, and completeness
    - Return quality score (0-100) and improvement suggestions
    - _Requirements: 3.3, 3.6, 8.1_

- [ ] 4. Implement Content Agent tools
  - [ ] 4.1 Create fact checker tool
    - Create backend/orchestrator/tools/content_tools.py
    - Implement FactCheckerTool using web search
    - Verify claims against web sources
    - Return verification results with confidence scores
    - _Requirements: 4.1, 4.4, 12.1, 12.4_
  
  - [ ] 4.2 Create content length validator tool
    - Implement LengthValidatorTool in content_tools.py
    - Ensure bullet points are 10-15 words maximum
    - Return validation results with word counts
    - _Requirements: 4.2, 4.5_
  
  - [ ] 4.3 Create bullet point quality scorer tool
    - Implement BulletQualityScorer in content_tools.py
    - Evaluate clarity, impact, and specificity
    - Return quality score (0-100) per bullet point
    - _Requirements: 4.3, 4.6, 8.1_

- [ ] 5. Implement Reviewer Agent tools
  - [ ] 5.1 Create grammar checker tool
    - Create backend/orchestrator/tools/reviewer_tools.py
    - Implement GrammarCheckerTool using language_tool_python or simple rules
    - Identify grammatical errors and suggest corrections
    - _Requirements: 5.1, 5.4_
  
  - [ ] 5.2 Create redundancy detector tool
    - Implement RedundancyDetectorTool in reviewer_tools.py
    - Identify repeated information across slides
    - Return redundancy report with suggestions
    - _Requirements: 5.2, 5.5_
  
  - [ ] 5.3 Create tone consistency validator tool
    - Implement ToneValidatorTool in reviewer_tools.py
    - Verify consistent tone throughout presentation
    - Return consistency score (0-100) and flagged sections
    - _Requirements: 5.3, 5.6, 8.1_

- [ ] 6. Implement Design Agent tools
  - [ ] 6.1 Create layout recommendation engine tool
    - Create backend/orchestrator/tools/design_tools.py
    - Implement LayoutRecommenderTool
    - Suggest layouts based on content structure (bullet_list, two_column, title_only, image_placeholder)
    - _Requirements: 6.1, 6.4_
  
  - [ ] 6.2 Create visual balance checker tool
    - Implement BalanceCheckerTool in design_tools.py
    - Evaluate content distribution across slides
    - Return balance score (0-100) and recommendations
    - _Requirements: 6.2, 6.5, 8.1_
  
  - [ ] 6.3 Create speaker notes generator tool
    - Implement NotesGeneratorTool in design_tools.py
    - Generate 2-3 sentence speaker notes for each slide
    - _Requirements: 6.3, 6.6_

- [ ] 7. Checkpoint - Verify all tools are implemented and tested
  - Ensure all 12 tools are created and functional
  - Verify tool error handling works correctly
  - Test tool registry can discover all tools
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement ReAct Planner Agent
  - [ ] 8.1 Refactor backend/orchestrator/planner_agent.py to use AgentExecutor
    - Replace simple chain with create_react_agent
    - Configure AgentExecutor with Groq LLM
    - Register Planner tools (WebSearch, StructureValidator, QualityChecker)
    - Add conversation memory integration
    - Implement quality threshold checking (stop when quality >= threshold)
    - Add max_iterations limit (3-5 iterations)
    - Add reasoning trace logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 7.1, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 14.1, 14.2, 14.3_
  
  - [ ]* 8.2 Write unit tests for Planner Agent
    - Test agent initialization with Groq API
    - Test tool registration and invocation
    - Test reasoning loop iteration
    - Test quality threshold early stopping
    - Test max iterations limit
    - _Requirements: 2.1, 2.2, 8.1, 8.3, 8.4, 8.5_

- [ ] 9. Implement ReAct Content Agent
  - [ ] 9.1 Refactor backend/orchestrator/content_agent.py to use AgentExecutor
    - Replace simple chain with create_react_agent
    - Configure AgentExecutor with Groq LLM
    - Register Content tools (FactChecker, LengthValidator, QualityScorer)
    - Add conversation memory integration
    - Add access to cached Planner results
    - Implement quality threshold checking
    - Add max_iterations limit (3-5 iterations)
    - Add reasoning trace logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 14.1, 14.2, 14.3_
  
  - [ ]* 9.2 Write unit tests for Content Agent
    - Test agent initialization with Groq API
    - Test tool registration and invocation
    - Test reasoning loop iteration
    - Test quality threshold early stopping
    - Test access to cached Planner results
    - _Requirements: 2.1, 2.2, 7.4, 8.1, 8.3, 8.4_

- [ ] 10. Implement ReAct Reviewer Agent
  - [ ] 10.1 Refactor backend/orchestrator/reviewer_agent.py to use AgentExecutor
    - Replace simple chain with create_react_agent
    - Configure AgentExecutor with Groq LLM
    - Register Reviewer tools (GrammarChecker, RedundancyDetector, ToneValidator)
    - Add conversation memory integration
    - Add access to cached Content results
    - Implement quality threshold checking
    - Add max_iterations limit (3-5 iterations)
    - Add reasoning trace logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 5.1, 5.2, 5.3, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 14.1, 14.2, 14.3_
  
  - [ ]* 10.2 Write unit tests for Reviewer Agent
    - Test agent initialization with Groq API
    - Test tool registration and invocation
    - Test reasoning loop iteration
    - Test quality threshold early stopping
    - Test access to cached Content results
    - _Requirements: 2.1, 2.2, 7.4, 8.1, 8.3, 8.4_

- [ ] 11. Implement ReAct Design Agent
  - [ ] 11.1 Refactor backend/orchestrator/design_agent.py to use AgentExecutor
    - Replace simple chain with create_react_agent
    - Configure AgentExecutor with Groq LLM
    - Register Design tools (LayoutRecommender, BalanceChecker, NotesGenerator)
    - Add conversation memory integration
    - Add access to cached Reviewer results
    - Implement quality threshold checking
    - Add max_iterations limit (3-5 iterations)
    - Add reasoning trace logging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.1, 6.2, 6.3, 7.1, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 14.1, 14.2, 14.3_
  
  - [ ]* 11.2 Write unit tests for Design Agent
    - Test agent initialization with Groq API
    - Test tool registration and invocation
    - Test reasoning loop iteration
    - Test quality threshold early stopping
    - Test access to cached Reviewer results
    - _Requirements: 2.1, 2.2, 7.4, 8.1, 8.3, 8.4_

- [ ] 12. Update orchestrator for ReAct agents
  - [ ] 12.1 Update backend/orchestrator/orchestrator.py
    - Initialize memory system at pipeline start
    - Pass memory to all agents
    - Update agent invocation to handle AgentExecutor responses
    - Add iteration count and quality score logging
    - Preserve existing timeout and error handling
    - Preserve fallback mechanisms for timeout scenarios
    - Clear memory cache after pipeline completion
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 12.5, 14.3, 14.4_
  
  - [ ]* 12.2 Write integration tests for orchestrator
    - Test full pipeline execution with ReAct agents
    - Test memory persistence across agents
    - Test timeout handling with AgentExecutor
    - Test error handling and fallback mechanisms
    - _Requirements: 7.5, 9.1, 9.2, 9.3, 9.4, 12.1, 12.5_

- [ ] 13. Checkpoint - Verify backward compatibility
  - Run existing test suite (backend/tests/)
  - Verify all existing tests pass without modification
  - Test API interface compatibility
  - Test PresentationContent model compatibility
  - Verify error handling patterns preserved
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 14. Performance optimization and monitoring
  - [ ] 14.1 Add performance logging
    - Log execution time for each agent
    - Log total pipeline duration
    - Log iteration counts per agent
    - Log quality scores per agent
    - Log tool invocation counts and durations
    - _Requirements: 8.6, 10.1, 10.2, 10.3, 10.4, 10.5, 14.3, 14.4_
  
  - [ ] 14.2 Implement Groq API error handling
    - Handle rate limit errors with descriptive messages
    - Handle service unavailable errors
    - Handle timeout errors
    - Add retry logic for transient failures
    - _Requirements: 1.5, 12.1, 12.2, 12.3, 12.5_
  
  - [ ]* 14.3 Create performance comparison tests
    - Compare execution time vs Ollama implementation
    - Compare output quality vs Ollama implementation
    - Document performance improvements
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 15. Documentation and configuration
  - [ ] 15.1 Update configuration documentation
    - Document Groq API setup in README
    - Document environment variables (GROQ_API_KEY, GROQ_MODEL, MAX_ITERATIONS, QUALITY_THRESHOLD)
    - Document model selection options
    - Document quality threshold tuning
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ] 15.2 Add logging documentation
    - Document reasoning trace format
    - Document tool invocation logging
    - Document quality score interpretation
    - Document performance metrics
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 16. Final integration and validation
  - [ ] 16.1 End-to-end testing
    - Test complete presentation generation with various topics
    - Test different tone parameters (formal, casual, professional)
    - Test different slide counts (5, 10, 15, 20)
    - Verify reasoning traces are logged correctly
    - Verify quality thresholds work as expected
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.6, 14.1_
  
  - [ ] 16.2 Verify Python 3.9 compatibility
    - Test on Python 3.9 environment
    - Verify async syntax compatibility (asyncio.wait_for)
    - Verify type hints compatibility
    - Verify all dependencies install correctly
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ]* 16.3 Performance benchmarking
    - Run performance comparison tests
    - Document speed improvements over Ollama
    - Document quality improvements
    - Create performance report
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 17. Final checkpoint - Complete system validation
  - Verify all requirements are met
  - Verify all tests pass
  - Verify backward compatibility maintained
  - Verify performance improvements achieved
  - Verify logging and observability working
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- The implementation maintains backward compatibility throughout
- ReAct agents will autonomously decide when to use tools based on task needs
- Quality thresholds enable early stopping when output is sufficient
- Memory systems enable context sharing across the agent pipeline
- Groq API provides significantly faster inference than local Ollama
