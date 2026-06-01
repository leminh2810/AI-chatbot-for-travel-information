# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nông Đức Hoàng
- **Student ID**: 2A202600580
- **Date**: June 01, 2026

---

## I. Technical Contribution (15 Points)

My primary responsibility in this lab was Layer 3 (Model Connection), focusing on the integration, management, and fallback mechanisms for different Large Language Models.

- **Modules Implemented**: 
  - `src/core/openai_provider.py`
  - `src/core/gemini_provider.py`
  - `src/core/fallback_provider.py`
- **Code Highlights**: I successfully implemented the Provider Switching mechanism (OpenAI -> Gemini) allowing the system to handle API failures gracefully and compare latency between models.
- **Documentation**: My code interacts with the ReAct loop by acting as a robust abstraction layer. When the Agent needs to generate a `Thought` or `Action`, it calls the provider interface. If the primary model (e.g., OpenAI) times out or hits a rate limit, the `fallback_provider.py` automatically routes the prompt to the secondary model (e.g., Gemini) without breaking the Agent's reasoning cycle.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: During the execution of the ReAct loop, the parser frequently failed because the LLM outputted markdown backticks instead of raw JSON. This caused the system to crash when attempting to extract the `Action` and `Action Input`.
- **Log Source**: Analyzed from `LOG_EVENT: LLM_METRIC` in the `logs/` directory, which revealed the exact raw text response returned by the models before parsing.
- **Diagnosis**: The LLM models (especially when switching between OpenAI and Gemini) have different default tendencies for formatting JSON. The issue stemmed from the model's behavior, not the tool specification.
- **Solution**: I resolved this by instructing the LLM specifically in the system prompt to "Only output raw JSON" without markdown formatting. Additionally, I added a preprocessing step in the provider layer to strip any markdown backticks before passing the string to the Agent's parser.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: The `Thought` block significantly enhanced the agent's capability compared to a direct Chatbot because it allowed the model to plan multi-step queries (e.g., calculating total cost after finding a price and applying tax) rather than guessing the final answer in one go.
2.  **Reliability**: The Agent actually performed worse than the Chatbot in simple Q&A scenarios. The ReAct loop introduces unnecessary overhead, latency, and a higher risk of parsing errors for straightforward questions that don't require external tool usage.
3.  **Observation**: Environment feedback (observations) was crucial for iterative refinement; for example, when a tool returned "No data found", the observation forced the agent to react to the failure and try an alternative approach instead of hallucinating an answer.

---

## IV. Future Improvements (5 Points)

To scale this system for a production-level AI agent, I propose the following improvements:

- **Scalability**: Use an asynchronous queue for tool calls to prevent the main thread from blocking during long network requests.
- **Safety**: Implement a 'Supervisor' LLM to audit the agent's actions before executing sensitive tools. 
- **Performance**: Incorporate a Vector DB for tool retrieval in a many-tool system to dynamically load only the most relevant tool descriptions into the prompt context.