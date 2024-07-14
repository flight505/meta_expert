from langchain_core.messages import AIMessage

from typing import List, Dict

def get_ai_message_contents(conversation_history: List[Dict[str, str]]) -> List[str]:
    if conversation_history is None:
        return []
    return [message['content'] for message in conversation_history if message.get('role') == 'assistant']
