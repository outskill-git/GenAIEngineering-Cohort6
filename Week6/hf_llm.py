from __future__ import annotations

import json
import os
import re
from types import SimpleNamespace

from transformers import pipeline


_PIPELINE_CACHE = {}
_MODEL_ALIASES = {
    # Old notebook model names mapped to lightweight local HF defaults.
    "llama-3.3-70b-versatile": "google/flan-t5-small",
    "openai/gpt-oss-120b": "google/flan-t5-small",
}
_DEFAULT_MODEL = os.getenv("WEEK6_HF_CHAT_MODEL", "google/flan-t5-small")
_GEMINI_MODEL = os.getenv("WEEK6_GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")
_PIPELINE_TASKS = os.getenv("WEEK6_HF_PIPELINE_TASKS", "text-generation,text2text-generation")


def _allow_remote_models() -> bool:
    return os.getenv("WEEK6_ALLOW_REMOTE_MODELS", "0").lower() in {"1", "true", "yes"}


def _resolve_model(model_name: str | None) -> str:
    if not model_name:
        return _DEFAULT_MODEL

    key = str(model_name)
    if _allow_remote_models():
        return key

    return _MODEL_ALIASES.get(key, _MODEL_ALIASES.get(key.lower(), key))


def _is_groq_model(model_name: str) -> bool:
    if not _allow_remote_models():
        return False

    lowered = model_name.lower()
    return (
        lowered.startswith("groq:")
        or lowered.startswith("groq/")
        or lowered in {"llama-3.3-70b-versatile", "mixtral", "openai/gpt-oss-120b"}
        or lowered.startswith("openai/")
    )


def _is_gemini_model(model_name: str) -> bool:
    if not _allow_remote_models():
        return False

    return "gemini" in model_name.lower()


def _groq_chat_completion(messages, model, temperature, max_tokens, tools=None, tool_choice=None, **kwargs):
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    request = {
        "messages": messages,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:
        request["tools"] = tools
        request["tool_choice"] = tool_choice or "auto"

    completion = client.chat.completions.create(**request)

    # Groq's own message object already exposes .content and .tool_calls, and can
    # be appended straight back into the message history for the next turn.
    # Only normalise content, which is None on a pure tool-call response.
    message = completion.choices[0].message
    if message.content is None:
        message.content = ""

    return completion


def _gemini_chat_completion(messages, model, temperature, max_tokens, **kwargs):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
    contents = []
    system_instruction = None

    for message in messages:
        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        if role == "system":
            system_instruction = content
            continue
        contents.append(
            types.Content(
                role="user" if role == "user" else "model",
                parts=[types.Part(text=content)],
            )
        )

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    message_obj = SimpleNamespace(content=response.text or "", tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message_obj)])


def _get_pipeline(model_name: str):
    if model_name not in _PIPELINE_CACHE:
        last_err = None
        task_candidates = []
        seen = set()
        for task in _PIPELINE_TASKS.split(","):
            task = task.strip()
            if task and task not in seen:
                task_candidates.append(task)
                seen.add(task)

        for task in ["text-generation", "text2text-generation", "any-to-any"]:
            if task not in seen:
                task_candidates.append(task)

        for task in task_candidates:
            try:
                _PIPELINE_CACHE[model_name] = pipeline(task, model=model_name)
                break
            except Exception as exc:
                last_err = exc

        if model_name not in _PIPELINE_CACHE:
            raise RuntimeError(f"Unable to initialize HF pipeline for model {model_name}: {last_err}") from last_err

    return _PIPELINE_CACHE[model_name]


def _messages_to_prompt(messages, tools=None):
    sections = []

    for message in messages:
        role = message.get("role", "user").upper()
        content = str(message.get("content", "")).strip()
        if not content:
            continue

        if role == "TOOL":
            sections.append(f"TOOL RESULT ({message.get('name', 'tool')}): {content}")
        else:
            sections.append(f"{role}: {content}")

    if tools:
        tool_names = []
        for t in tools:
            fn = t.get("function", {})
            if fn.get("name"):
                tool_names.append(fn.get("name"))

        if not tool_names:
            tool_names = ["Get_Data"]

        tool_names_json = json.dumps(tool_names)
        sections.append(
            "You can use tool(s) only if helpful.\n"
            f"Tool names: {tool_names_json}.\n"
            "If using tools, return STRICT JSON only: \n"
            '{"tool_calls":[{"id":"tc_1","type":"function","function":{"name":"Get_Data","arguments":"{\\\"SQL_Query\\\":\\\"...\\\"}"}}]}\n'
            "If no tool is needed, return a plain assistant response."
        )

    return "\n".join(sections) + "\nASSISTANT:"


def _safe_json(payload: str):
    try:
        return json.loads(payload)
    except Exception:
        return None


def _extract_json_candidates(text: str):
    blocks = re.findall(r"```(?:json)?\n(.*?)```", text, re.S)
    if blocks:
        for block in blocks:
            candidate = _safe_json(block.strip())
            if candidate is not None:
                yield candidate

    candidate = _safe_json(text.strip())
    if candidate is not None:
        yield candidate


def _extract_tool_calls(text: str):
    for candidate in _extract_json_candidates(text):
        if isinstance(candidate, dict) and isinstance(candidate.get("tool_calls"), list):
            return [_coerce_tool_call(entry, idx) for idx, entry in enumerate(candidate.get("tool_calls", []))]

        if isinstance(candidate, dict) and candidate.get("name"):
            return [_coerce_tool_call(candidate, 0)]

    # simple fallback: look for SQL pattern
    sql_match = re.search(r"SELECT .*?", text, re.S)
    if sql_match:
        args = json.dumps({"SQL_Query": sql_match.group(0).strip()})
        return [_coerce_tool_call({"name": "Get_Data", "arguments": args}, 0)]

    return None


def _coerce_tool_call(entry: dict, index: int):
    call_id = entry.get("id", f"tc_{index + 1}")
    function_name = entry.get("name") or entry.get("function", {}).get("name")
    arguments = entry.get("arguments")

    if function_name is None:
        function_name = "Get_Data"

    if arguments is None:
        args_payload = entry.get("function", {})
        if isinstance(args_payload, dict) and "arguments" in args_payload:
            arguments = args_payload.get("arguments")
        else:
            arguments = json.dumps(args_payload)

    if isinstance(arguments, dict):
        arguments = json.dumps(arguments)

    if not isinstance(arguments, str):
        arguments = json.dumps({"SQL_Query": str(arguments)})

    function_obj = SimpleNamespace(name=function_name, arguments=arguments)
    return SimpleNamespace(id=call_id, function=function_obj)


def hf_chat_completion(
    messages,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 512,
    tools=None,
    **kwargs,
):
    model_name = _resolve_model(model)

    if _is_groq_model(model_name) and os.getenv("GROQ_API_KEY"):
        return _groq_chat_completion(
            messages,
            model_name,
            temperature,
            max_tokens,
            tools=tools,
            **kwargs,
        )

    if _is_gemini_model(model_name) and os.getenv("GENAI_API_KEY"):
        return _gemini_chat_completion(
            messages,
            model_name,
            temperature,
            max_tokens,
            **kwargs,
        )

    generator = _get_pipeline(model_name)

    prompt = _messages_to_prompt(messages, tools=tools)
    generated = generator(
        prompt,
        max_new_tokens=max_tokens,
        do_sample=temperature > 0,
        temperature=temperature,
        **{k: v for k, v in kwargs.items() if k in {"top_p", "top_k", "repetition_penalty"}},
    )[0]["generated_text"]

    text = str(generated).replace(prompt, "", 1).strip()

    tool_calls = None
    if tools:
        tool_calls = _extract_tool_calls(text)
        if tool_calls:
            content = ""
        else:
            content = text
    else:
        content = text

    message_obj = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice_obj = SimpleNamespace(message=message_obj)
    return SimpleNamespace(choices=[choice_obj])
