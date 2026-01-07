"""
CrewAI Integration Example for AgentTrace

This example demonstrates how to use AgentTrace with CrewAI.
"""

import os
from crewai import Agent, Task, Crew
from langchain.llms import OpenAI
from agenttrace.integrations.crewai import CrewAITracer

# Initialize AgentTrace tracer
tracer = CrewAITracer(
    api_key=os.getenv("AGENTTRACE_API_KEY", "your-api-key"),
    project="crewai-example",
    api_url=os.getenv("AGENTTRACE_API_URL", "http://localhost:8000"),
    environment="development"
)

# Create LLM
llm = OpenAI(temperature=0.7)

# Create agents
researcher = Agent(
    role="Research Analyst",
    goal="Research and analyze AI trends",
    backstory="You are an expert AI researcher with deep knowledge of machine learning.",
    llm=llm,
    verbose=True
)

writer = Agent(
    role="Content Writer",
    goal="Write engaging content about AI",
    backstory="You are a skilled technical writer who can explain complex topics simply.",
    llm=llm,
    verbose=True
)

# Create tasks
research_task = Task(
    description="Research the latest trends in AI observability",
    agent=researcher
)

writing_task = Task(
    description="Write a brief summary of AI observability trends",
    agent=writer
)

# Create crew with AgentTrace callback
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    callbacks=[tracer],
    verbose=True
)

# Run the crew
if __name__ == "__main__":
    print("Running CrewAI with AgentTrace...\n")

    result = crew.kickoff()

    print("\n" + "="*50)
    print("RESULT")
    print("="*50)
    print(result)
    print("\n✓ Trace sent to AgentTrace!")
    print("View your traces at: http://localhost:3000")
