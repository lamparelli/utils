# make sure libraries are installed
try:
    import langchain
except Exception:
    raise ImportError("Missing package. Please launch `pip install langchain`.")
try:
    import langchain_core
except Exception:
    raise ImportError("Missing package. Please launch `pip install langchain-core`.")
try:
    import pydantic
except Exception:
    raise ImportError("Missing package. Please launch `pip install pydantic`.")

# imports
import os
from typing import Literal
from pydantic import BaseModel
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def _init_llm(
    model_provider: Literal['openai', 'google_genai'], 
    model_name: str, 
    pydantic_output_schema: BaseModel,
    model_temperature: float, 
    timeout_per_attempt: int, 
    max_retries: int
):
    # make sure LLM library is installed and API key is set
    if model_provider == 'google_genai':
        try:
            import langchain_google_genai
        except Exception:
            raise ImportError("Missing package. Please launch `pip install langchain-google-genai`.")
        if "GOOGLE_API_KEY" not in os.environ:
            raise ValueError("Missing `GOOGLE_API_KEY`. Set os.environ['GOOGLE_API_KEY'] = 'MY_API_KEY'.")
    elif model_provider == 'openai':
        try:
            import langchain_openai
        except Exception:
            raise ImportError("Missing package. Please launch `pip install langchain-openai`.")
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("Missing `OPENAI_API_KEY`. Set os.environ['OPENAI_API_KEY'] = 'MY_API_KEY'.")
    else:
        raise ValueError(f"Model provider `{model_provider}` not supported. Pick one of ['openai', 'google_genai'].")
    
    # create LLM
    llm = init_chat_model(
        model_provider=model_provider,
        model=model_name,
        temperature=model_temperature,
        max_retries=max_retries,
        timeout=timeout_per_attempt
    )

    # check the output format
    is_pydantic_basemodel = isinstance(pydantic_output_schema, type) and issubclass(pydantic_output_schema, BaseModel)
    if not is_pydantic_basemodel:
        raise ValueError("Invalid value for param `pydantic_output_schema`. Expected type `BaseModel`, received type {type(pydantic_output_schema)}. Use the function `from pydantic import create_model` to create the pydantic_output_schema.")
    
    # convert to json mode
    llm_json = llm.with_structured_output(pydantic_output_schema)

    return llm_json

def generate_structured_output(
        model_provider: Literal['openai', 'google_genai'], 
        model_name: str, 
        system_prompt: str | SystemMessage,
        user_message: str | HumanMessage,
        pydantic_output_schema: BaseModel,
        model_temperature: float = 0.0, 
        timeout_per_attempt: int = 60, 
        max_retries: int = 1
    ):
        """Generates a JSON output (as defined by pydantic_output_schema) from a LLM model, given a system prompt and a user message.

        Args:
            model_provider (Literal['openai', 'google_genai']): The LLM provider
            model_name (str): The LLM model name
            system_prompt (str | SystemMessage): The system prompt
            user_message (str | HumanMessage): The user message
            pydantic_output_schema (BaseModel): The Pydantic output schema
            model_temperature (float, optional): The model temperature. Defaults to 0.0.
            timeout_per_attempt (int, optional): The timeout after which an attempt has to fail. Defaults to 60.
            max_retries (int, optional): The maximum number of retries in case of failure. Defaults to 1.

        Returns:
            BaseModel: The LLM response as a Pydantic object
        """

        # make sure messages are of correct type
        if isinstance(system_prompt, str):
            system_prompt = SystemMessage(content=system_prompt)
        if isinstance(user_message, str):
            user_message = HumanMessage(content=user_message)

        # get response
        llm_json = _init_llm(
            model_provider=model_provider,
            model_name=model_name,
            pydantic_output_schema=pydantic_output_schema,
            model_temperature=model_temperature,
            timeout_per_attempt=timeout_per_attempt,
            max_retries=max_retries
        )
        response = llm_json.invoke([system_prompt, user_message])

        return response

async def agenerate_structured_output(
        model_provider: Literal['openai', 'google_genai'], 
        model_name: str, 
        system_prompt: str | SystemMessage,
        user_message: str | HumanMessage,
        pydantic_output_schema: BaseModel,
        model_temperature: float = 0.0, 
        timeout_per_attempt: int = 60, 
        max_retries: int = 1
    ):
        """Generates a JSON output (as defined by pydantic_output_schema) from a LLM model, given a system prompt and a user message.

        Args:
            model_provider (Literal['openai', 'google_genai']): The LLM provider
            model_name (str): The LLM model name
            system_prompt (str | SystemMessage): The system prompt
            user_message (str | HumanMessage): The user message
            pydantic_output_schema (BaseModel): The Pydantic output schema
            model_temperature (float, optional): The model temperature. Defaults to 0.0.
            timeout_per_attempt (int, optional): The timeout after which an attempt has to fail. Defaults to 60.
            max_retries (int, optional): The maximum number of retries in case of failure. Defaults to 1.

        Returns:
            BaseModel: The LLM response as a Pydantic object
        """

        # make sure messages are of correct type
        if isinstance(system_prompt, str):
            system_prompt = SystemMessage(content=system_prompt)
        if isinstance(user_message, str):
            user_message = HumanMessage(content=user_message)

        # get response
        llm_json = _init_llm(
            model_provider=model_provider,
            model_name=model_name,
            pydantic_output_schema=pydantic_output_schema,
            model_temperature=model_temperature,
            timeout_per_attempt=timeout_per_attempt,
            max_retries=max_retries
        )
        response = await llm_json.ainvoke([system_prompt, user_message])

        return response
