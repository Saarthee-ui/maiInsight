from langchain import LLMChain, PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
 
# --- Step 1: Define Prompt Template for the Build Phase Agent ---
build_prompt = PromptTemplate(
    input_variables=["conversation_history", "user_input"],
    template="""
You are an AI assistant guiding a user through the 'Build' phase of an analytics automation setup.
 
Objective:
- Collect Process Initiation details: Database Name(s), Connection Type, Organization (Sales, Marketing, Finance, CX, HR, Technology, etc.), and Connection Details.
- Never collect passwords or credentials.
- If user wanders away, politely remind them of the goal: “Let's complete the Build setup first; we can return to other topics later.”
- Predict missing details and offer suggestions.
- Once all details are collected, summarize them clearly and ask for confirmation.
- When confirmed, trigger simulated actions: create folders, setup placeholders for connections, and mark phase as 'validated'.
 
Conversation so far:
{conversation_history}
 
User: {user_input}
AI:"""
)
 
# --- Step 2: Initialize Memory and Model ---
llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.3)
memory = ConversationBufferMemory(memory_key="conversation_history")
 
# --- Step 3: Define LLM Chain for Build Phase ---
build_phase_agent = LLMChain(
    llm=llm,
    prompt=build_prompt,
    memory=memory
)
 
# --- Step 4: Example Interaction Function ---
def run_build_phase(user_input):
    response = build_phase_agent.run(user_input=user_input)
    return response
 
# Example Usage
if __name__ == "__main__":
    print("AI Build Phase Agent Initialized...\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting Build Phase Agent.")
            break
        response = run_build_phase(user_input)
        print(f"Agent: {response}\n")