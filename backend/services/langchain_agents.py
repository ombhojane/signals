from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
import os
import json
from typing import Dict, Any, List


# Initialize LLMs with Groq
def get_groq_llm(model_name: str, temperature: float = 0.3) -> ChatGroq:
    """Initialize Groq LLM with specified model"""
    api_key = os.getenv("GROQ_API_KEY")
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        groq_api_key=api_key
    )


# Define analysis tools
@tool
def analyze_token_data(data: str) -> str:
    """
    Analyze cryptocurrency token data and provide insights on price trends, liquidity, and market activity.
    
    Args:
        data: JSON string containing token price and market data
    
    Returns:
        Detailed analysis of the token data
    """
    try:
        token_data = json.loads(data) if isinstance(data, str) else data
        
        # Extract key metrics for analysis
        analysis_prompt = f"""
        As a cryptocurrency data analyst, analyze the following token data and provide insights:
        
        Data: {json.dumps(token_data, indent=2)}
        
        Please provide:
        1. Price trend analysis
        2. Liquidity assessment
        3. Market activity insights
        4. Key risk factors
        5. Overall market sentiment
        
        Format your response as a structured analysis.
        """
        
        return analysis_prompt
    except Exception as e:
        return f"Error analyzing token data: {str(e)}"


@tool
def analyze_gmgn_data(data: str) -> str:
    """
    Analyze GMGN token data and provide investment insights.
    
    Args:
        data: JSON string containing GMGN token information
    
    Returns:
        Investment analysis and forecast
    """
    try:
        gmgn_data = json.loads(data) if isinstance(data, str) else data
        
        analysis_prompt = f"""
        As a GMGN data analyst, analyze the following token data:
        
        Data: {json.dumps(gmgn_data, indent=2)}
        
        Provide a brief analysis covering:
        1. Token fundamentals
        2. Investment potential assessment
        3. Risk evaluation
        4. Market position analysis
        5. Investment recommendation (without specific buy/sell advice)
        
        Focus on whether this token shows good investment characteristics.
        """
        
        return analysis_prompt
    except Exception as e:
        return f"Error analyzing GMGN data: {str(e)}"


@tool
def analyze_twitter_sentiment(data: str) -> str:
    """
    Analyze sentiment of tweets and provide insights with scoring.
    
    Args:
        data: JSON string containing tweet data
    
    Returns:
        Sentiment analysis with score from 0-100
    """
    try:
        tweets_data = json.loads(data) if isinstance(data, str) else data
        
        analysis_prompt = f"""
        As a Twitter sentiment analyst, analyze the following tweets:
        
        Data: {json.dumps(tweets_data, indent=2)}
        
        Provide:
        1. Overall sentiment analysis (positive/negative/neutral)
        2. Community mood assessment
        3. Key themes and topics
        4. Sentiment score from 0-100 (0=very negative, 50=neutral, 100=very positive)
        5. Impact on token perception
        
        Focus on how social sentiment might affect the token.
        """
        
        return analysis_prompt
    except Exception as e:
        return f"Error analyzing Twitter sentiment: {str(e)}"


@tool
def predict_token_movement(data: str) -> str:
    """
    Predict future token movement based on combined analysis data.
    
    Args:
        data: JSON string containing combined analysis data
    
    Returns:
        Prediction with action signal
    """
    try:
        combined_data = json.loads(data) if isinstance(data, str) else data
        
        prediction_prompt = f"""
        As a cryptocurrency prediction expert, analyze the combined data:
        
        Data: {json.dumps(combined_data, indent=2)}
        
        Based on all available information, provide:
        1. Future movement prediction
        2. Key factors influencing the prediction
        3. Confidence level
        4. Action signal: Choose ONE from [Strong Buy, Buy, Hold, Sell, Strong Sell]
        5. Risk assessment
        
        Be specific about the action signal recommendation.
        """
        
        return prediction_prompt
    except Exception as e:
        return f"Error predicting token movement: {str(e)}"


class LangChainAgents:
    """LangChain agents to replace CrewAI functionality"""
    
    def __init__(self):
        # Initialize different LLMs for different agents
        self.token_llm = get_groq_llm("llama-3.3-70b-versatile")
        self.gmgn_llm = get_groq_llm("llama-3.3-70b-versatile")
        self.twitter_llm = get_groq_llm("deepseek-r1-distill-llama-70b")
        self.predict_llm = get_groq_llm("llama3-8b-8192")
    
    def analyze_token_price(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze token price data using direct LLM call
        
        Args:
            data: Token price data dictionary
            
        Returns:
            Analysis result
        """
        try:
            data_str = json.dumps(data, indent=2)
            
            analysis_prompt = f"""
            As a cryptocurrency data analyst, analyze the following token data and provide insights:
            
            Data: {data_str}
            
            Please provide:
            1. Price trend analysis
            2. Liquidity assessment  
            3. Market activity insights
            4. Key risk factors
            5. Overall market sentiment
            
            Format your response as a structured analysis.
            """
            
            response = self.token_llm.invoke(analysis_prompt)
            
            return {
                "raw": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "raw": f"Error in token analysis: {str(e)}",
                "status": "error"
            }
    
    def analyze_gmgn_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze GMGN token information using direct LLM call
        
        Args:
            data: GMGN token data dictionary
            
        Returns:
            Analysis result
        """
        try:
            data_str = json.dumps(data, indent=2)
            
            analysis_prompt = f"""
            As a GMGN data analyst, analyze the following token data:
            
            Data: {data_str}
            
            Provide a brief analysis covering:
            1. Token fundamentals
            2. Investment potential assessment
            3. Risk evaluation
            4. Market position analysis
            5. Investment recommendation (without specific buy/sell advice)
            
            Focus on whether this token shows good investment characteristics.
            """
            
            response = self.gmgn_llm.invoke(analysis_prompt)
            
            return {
                "raw": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "raw": f"Error in GMGN analysis: {str(e)}",
                "status": "error"
            }
    
    def analyze_twitter_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Twitter sentiment data using direct LLM call
        
        Args:
            data: Twitter data dictionary
            
        Returns:
            Sentiment analysis result
        """
        try:
            data_str = json.dumps(data, indent=2)
            
            analysis_prompt = f"""
            As a Twitter sentiment analyst, analyze the following tweets:
            
            Data: {data_str}
            
            Provide:
            1. Overall sentiment analysis (positive/negative/neutral)
            2. Community mood assessment
            3. Key themes and topics
            4. Sentiment score from 0-100 (0=very negative, 50=neutral, 100=very positive)
            5. Impact on token perception
            
            Focus on how social sentiment might affect the token.
            """
            
            response = self.twitter_llm.invoke(analysis_prompt)
            
            return {
                "raw": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "raw": f"Error in Twitter sentiment analysis: {str(e)}",
                "status": "error"
            }
    
    def predict_movement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict token movement using direct LLM call
        
        Args:
            data: Combined analysis data dictionary
            
        Returns:
            Prediction result with action signal
        """
        try:
            data_str = json.dumps(data, indent=2)
            
            prediction_prompt = f"""
            As a cryptocurrency prediction expert, analyze the combined data:
            
            Data: {data_str}
            
            Based on all available information, provide:
            1. Future movement prediction
            2. Key factors influencing the prediction
            3. Confidence level
            4. Action signal: Choose ONE from [Strong Buy, Buy, Hold, Sell, Strong Sell]
            5. Risk assessment
            
            Be specific about the action signal recommendation.
            """
            
            response = self.predict_llm.invoke(prediction_prompt)
            
            return {
                "raw": response.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "raw": f"Error in prediction: {str(e)}",
                "status": "error"
            }


# Initialize global agents instance
agents = LangChainAgents()

# Export agent functions for backward compatibility
def analyze_token_price_agent(data):
    """Backward compatible function for token price analysis"""
    return agents.analyze_token_price(data)

def analyze_gmgn_agent(data):
    """Backward compatible function for GMGN analysis"""
    return agents.analyze_gmgn_info(data)

def analyze_twitter_agent(data):
    """Backward compatible function for Twitter analysis"""
    return agents.analyze_twitter_data(data)

def predict_movement_agent(data):
    """Backward compatible function for movement prediction"""
    return agents.predict_movement(data)
