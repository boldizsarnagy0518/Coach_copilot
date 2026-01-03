import pydantic_ai.models.openai
import inspect

print("Dir of pydantic_ai.models.openai:")
print(dir(pydantic_ai.models.openai))

try:
    from pydantic_ai.providers import OpenAIProvider

    print("\nOpenAIProvider found in pydantic_ai.providers")
except ImportError:
    print("\nOpenAIProvider NOT found in pydantic_ai.providers")

try:
    from pydantic_ai.models.openai import OpenAIProvider

    print("\nOpenAIProvider found in pydantic_ai.models.openai")
except ImportError:
    print("\nOpenAIProvider NOT found in pydantic_ai.models.openai")
