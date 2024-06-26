from chainlit import logger
import config as cfg
import chainlit as cl
from chainlit.input_widget import Select, Switch, Slider

from libs.ai import setup_chain
import libs.ai as ai
from langchain.schema.runnable.config import RunnableConfig

from libs.utils import *


@cl.on_chat_start
async def on_chat_start():
    """
    Initial setup run on start AND on new chat, setting up:
    * logging (loguru via lib/utils.py)
    * chain (from lib/ai.py), store in chainlit user_session
    """
    try:
        settings = await setup_chat_settings()
        setup_logging(settings["logging_level"])
        chain, chain_history = setup_chain()
        cl.user_session.set("chain", chain)
        cl.user_session.set("chain_history", chain_history)
        logger.info("OpenChatBot setup complete")
    except Exception as e:
        logger.error(f"Error during setup: {e}")


@cl.on_settings_update
async def on_settings_update():
    try:
        settings = await setup_chat_settings()
        setup_logging(settings["logging_level"])
        # chain = setup_chain()  # Setup the chain
        # cl.user_session.set("chain", chain)  # Save the chain to the chainlit user_session
        # cl.user_session.set("chain", chain)  # Save the chain to the chainlit user_session
        logger.info("OpenChatBot settings update complete")
    except Exception as e:
        logger.error(f"Error during setup: {e}")
    # logger.info("Exiting")


@cl.on_message
async def on_message(message: cl.Message):
    logger.info("Entered")
    chain = cl.user_session.get("chain")  # 1. Retrieve chain from user session
    chain_history = cl.user_session.get("chain_history")
    msg = cl.Message(content="")

    answer_prefix_tokens = ["FINAL", "ANSWER"]
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True,
        answer_prefix_tokens=answer_prefix_tokens,
    )

    async for chunk in chain.astream(  # 2. Run the chain aynchronously
        {
            "question": message.content,
            "system_persona": cfg.SYSTEM_PERSONA,
        },
        # {"configurable": {"session_id": "unused", "stream_final_answer": True}},
        config=RunnableConfig(
            callbacks=[cb],
            configurable={"session_id": chain_history},
        ),
    ):
        await msg.stream_token(chunk)
    await msg.send()
    cb.answer_reached = True
    logger.info("Exited")


async def setup_chat_settings():
    """
    Setup the chat settings, everything else from config.py
    """
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Ollama - Model",
                values=["mistral", "llama2"],
                initial_index=0,
            ),
            Select(
                id="bot_type",
                label="Bot Type",
                values=["chatbot_llm", "chabot_rag"],
                initial_index=1,
            ),
            Select(
                id="logging_level",
                label="Logging Level",
                values=[
                    "TRACE",
                    "DEBUG",
                    "INFO",
                    "SUCCESS",
                    "WARNING",
                    "ERROR",
                    "CRITICAL",
                ],
                initial_index=1,
            ),
            Switch(
                id="Streaming",
                label="Stream Tokens",
                initial=True,
            ),
            Slider(
                id="Temperature",
                label="Ollama - Temperature",
                initial=1,
                min=0,
                max=2,
                step=0.1,
            ),
        ]
    ).send()
    return settings
    # await setup_agent(settings)
