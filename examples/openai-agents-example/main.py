"""
OpenAI Agents Integration Example for AgentTrace

This example demonstrates how to use AgentTrace with OpenAI Assistants API.
"""

import os
import time
from openai import OpenAI
from agenttrace import AgentTrace

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize AgentTrace
trace = AgentTrace(
    api_key=os.getenv("AGENTTRACE_API_KEY", "your-api-key"),
    project="openai-agents-example",
    api_url=os.getenv("AGENTTRACE_API_URL", "http://localhost:8000"),
    environment="development"
)


@trace.trace_agent(name="openai-assistant")
def run_assistant(instructions: str, user_message: str):
    """Run an OpenAI Assistant with AgentTrace tracking"""

    # Create assistant
    assistant = client.beta.assistants.create(
        name="Math Tutor",
        instructions=instructions,
        model="gpt-4-turbo-preview",
        tools=[{"type": "code_interpreter"}]
    )

    # Create thread
    thread = client.beta.threads.create()

    # Add message
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Wait for completion
    while run.status in ["queued", "in_progress"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Get messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    # Clean up
    client.beta.assistants.delete(assistant.id)

    return {
        "status": run.status,
        "messages": [msg.content[0].text.value for msg in messages.data]
    }


if __name__ == "__main__":
    print("Running OpenAI Assistant with AgentTrace...\n")

    instructions = "You are a helpful math tutor. Guide students step-by-step."
    question = "Solve the equation: 3x + 11 = 14"

    print(f"Question: {question}\n")

    result = run_assistant(instructions, question)

    print("Status:", result["status"])
    print("\nMessages:")
    for i, msg in enumerate(result["messages"], 1):
        print(f"\n{i}. {msg}")

    print("\n✓ Trace sent to AgentTrace!")
    print("View your traces at: http://localhost:3000")
