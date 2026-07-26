"""
Multi-Agent CrewAI Experiment

A Python-based multi-agent setup using CrewAI for collaborative task execution.
"""

from crewai import Agent, Task, Crew, Process


# --- Define Agents ---

researcher = Agent(
    role="Researcher",
    goal="Find and synthesize relevant information from available sources",
    backstory="Expert researcher with deep analytical skills and attention to detail.",
    verbose=True,
    allow_delegation=False,
)

writer = Agent(
    role="Writer",
    goal="Transform research into clear, actionable reports",
    backstory="Skilled technical writer who excels at making complex topics accessible.",
    verbose=True,
    allow_delegation=False,
)

# --- Define Tasks ---

research_task = Task(
    description="Research the latest advancements in AI agent frameworks.",
    expected_output="A bullet-point summary of key findings with source references.",
    agent=researcher,
)

writing_task = Task(
    description="Write a concise report based on the research findings.",
    expected_output="A well-structured markdown report suitable for stakeholders.",
    agent=writer,
    context=[research_task],
)

# --- Assemble Crew ---

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    verbose=True,
)


def main():
    """Entry point for the multi-agent crew experiment."""
    print("🚀 Launching Multi-Agent Crew...")
    result = crew.kickoff()
    print("\n=== CREW OUTPUT ===")
    print(result)
    return result


if __name__ == "__main__":
    main()
