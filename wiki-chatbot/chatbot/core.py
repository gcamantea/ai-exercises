import boto3
from botocore.client import Config
from langchain_aws import ChatBedrock
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger(__name__)

class ChatbotCore:
    def __init__(self, model_id, kb_id):
        self.model_id = model_id
        self.kb_id = kb_id
        
        # Initialize Bedrock client
        session = boto3.session.Session()
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=session.region_name)
        
        # Initialize LLM and retriever
        self.llm = ChatBedrock(model_id=self.model_id, client=self.bedrock_client)
        self.retriever = self._initialize_retriever()

    def _initialize_retriever(self):
        return AmazonKnowledgeBasesRetriever(
            knowledge_base_id=self.kb_id,
            retrieval_config={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                    "overrideSearchType": "SEMANTIC"
                }
            }
        )

    def _create_system_message(self):
        return {
            "role": "system",
            "content": [{
                "type": "text",
                "text": "You are a helpful assistant that answers questions based on the provided context and previous conversation history. Do not make mentions of the context provided, or even that there is context provided. Just answer the question."
            }]
        }

    def _format_history_messages(self, history):
        return [
            {
                "role": h["role"],
                "content": [{"type": "text", "text": h["content"]}]
            }
            for h in history
        ]

    def _create_chat_prompt(self, history):
        messages = [self._create_system_message()]
        messages.extend(self._format_history_messages(history))
        messages.append({
            "role": "user",
            "content": [{
                "type": "text",
                "text": "Context: {context}\n\nQuestion: {input}\n\nAnswer the question based on the context provided."
            }]
        })
        return ChatPromptTemplate.from_messages(messages)

    def _generate_search_query(self, history, current_question):
        try:
            formatted_history = "\n".join([
                f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
                for h in history
            ])

            query_prompt = ChatPromptTemplate.from_messages([
                {
                    "role": "system",
                    "content": [{
                        "type": "text",
                        "text": "You are a search query optimizer. Generate a single, specific search query. "
                                "When you lack information to build a good search query, just return the user's question. "
                                "The current question is the most important part of the search query. use the conversation history just to contextualize the question. "
                                "Return only the search query, no other text."
                    }]
                },
                {
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": f"Conversation History:\n{formatted_history}\n\nCurrent Question: {current_question}"
                    }]
                }
            ])

            response = self.llm.invoke(query_prompt.format_messages())
            search_query = response.content.strip()
            
            # Log the search query generation
            logger.info(f"Generated search query (last 500 chars): ...{search_query[-500:]}")
            return search_query
        except Exception as e:
            logger.error(f"Error generating search query: {str(e)}")
            return current_question

    def generate_response(self, user_message, conversation_history=None):
        """Main method to generate a response to a user message"""
        history = conversation_history or []
        
        # Generate optimized search query
        search_query = self._generate_search_query(history, user_message)
        
        # Create response chain
        document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=self._create_chat_prompt(history),
        )
        response_chain = create_retrieval_chain(
            retriever=self.retriever,
            combine_docs_chain=document_chain
        )
        
        # Generate response
        response = response_chain.invoke({"input": search_query})
        final_response = response["answer"]
        
        # Log the final response
        logger.info(f"Bedrock response (last 500 chars): ...{final_response[-500:]}")
        
        return final_response 