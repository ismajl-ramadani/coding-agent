from google.genai import types
import json

content = types.Content(role="user", parts=[types.Part(text="hello")])
data = content.model_dump(exclude_none=True)
print("exclude_none:", data)
print("json:", json.dumps(data))
