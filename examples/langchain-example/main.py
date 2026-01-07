"""
LangChain Integration Example for AgentTrace

This example demonstrates how to use AgentTrace with LangChain.
"""

import os
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from agenttrace.integrations.langchain import LangChainTracer

# Initialize AgentTrace tracer
tracer = LangChainTracer(
    api_key=os.getenv("AGENTTRACE_API_KEY", "your-api-key"),
    project="langchain-example",
    api_url=os.getenv("AGENTTRACE_API_URL", "http://localhost:8000"),
    environment="development"
)

# Create a simple LLM chain
llm = OpenAI(temperature=0.9)

template = """Question: {question}

Answer: Let's think step by step."""

prompt = PromptTemplate(template=template, input_variables=["question"])

# Create the chain with AgentTrace callback
chain = LLMChain(
    llm=llm,
    prompt=prompt,
    callbacks=[tracer]
)

# Run the chain
if __name__ == "__main__":
    question = "What are the key benefits of AI observability?"

    print(f"Question: {question}")
    print("\nRunning LangChain with AgentTrace...\n")

    result = chain.run(question)

    print(f"Answer: {result}")
    print("\n✓ Trace sent to AgentTrace!")
    print("View your traces at: http://localhost:3000")
