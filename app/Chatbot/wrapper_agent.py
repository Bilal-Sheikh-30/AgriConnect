from langchain_core.messages import HumanMessage, AIMessage
from app.Chatbot.Agent.agri_agent import get_agent_executor

# Store conversation history in memory (simple approach)
# For production, consider using a database or session storage
conversation_history = []

async def ask_agent(user_input: str, session_id: str = "default"):
    """
    Process user query through the agricultural agent.
    
    Args:
        user_input: User's question
        session_id: Session identifier for maintaining conversation history
    
    Returns:
        Agent's response as string
    """
    try:
        # Create Agent executor
        agent_executor = get_agent_executor()
        
        # Prepare messages with conversation history
        messages = []
        
        # Add conversation history (last 5 exchanges to keep context manageable)
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 5 exchanges (10 messages)
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        # Invoke Agent
        response = await agent_executor.ainvoke({
            "messages": messages,
            "agent_scratchpad": []
        })
        
        # Extract output
        output = response.get("output", "I apologize, but I couldn't process your request. Please try again.")
        
        # Store in conversation history
        conversation_history.append(HumanMessage(content=user_input))
        conversation_history.append(AIMessage(content=output))
        
        # Keep history manageable (last 20 messages = 10 exchanges)
        if len(conversation_history) > 20:
            conversation_history[:] = conversation_history[-20:]
        
        return output
        
    except Exception as e:
        print(f"Agent Error: {e}")
        return "I apologize, but I encountered an error. Please try rephrasing your question or ask about farming, crops, equipment, or AgriConnect platform features."

def clear_conversation_history():
    """Clear the conversation history - useful for new sessions"""
    conversation_history.clear()