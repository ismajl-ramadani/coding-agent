import os
import config
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import system_prompt
import argparse
from call_function import available_functions, call_function
import sys

load_dotenv()

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key is None:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables.")
    

    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    client = genai.Client(api_key=api_key)

    promt = args.user_prompt
    if args.verbose:
        print("User prompt:", promt)

    messages = [types.Content(role="user", parts=[types.Part(text=args.user_prompt)])]

    for iteration in range(20):
        generate_config = types.GenerateContentConfig(
            tools=[available_functions],
            system_instruction=system_prompt,
        )
        if config.IS_THINKING_MODEL:
            generate_config.thinking_config = types.ThinkingConfig(include_thoughts=True)

        response = client.models.generate_content(
            model=config.MODEL_ID,
            contents=messages,
            config=generate_config,
        )

        if response.usage_metadata is not None and args.verbose:
            print(f"[Loop {iteration + 1}] Prompt tokens: {response.usage_metadata.prompt_token_count} | Response tokens: {response.usage_metadata.candidates_token_count}")

        if response.candidates:
            for candidate in response.candidates:
                messages.append(candidate.content)

        if response.function_calls:
            # We need to save the results of these executions for the next lesson
            function_results = []
            
            for function_call in response.function_calls:
                # Execute it
                function_call_result = call_function(function_call, verbose=args.verbose)
                
                # Strict validation checks
                if not function_call_result.parts:
                    raise ValueError("Function call result has no parts.")
                
                func_response = function_call_result.parts[0].function_response
                if func_response is None:
                    raise ValueError("Function call result has no function_response.")
                
                if func_response.response is None:
                    raise ValueError("Function response has no response data.")
                
                # Save the successful part to our list
                function_results.append(function_call_result.parts[0])

                # Print out what actually happened if we are in verbose mode
                if args.verbose:
                    # Truncate long outputs for terminal readability if desired, but printing the whole thing is fine too
                    output_text = str(func_response.response)
                    if len(output_text) > 200:
                        print(f"-> {output_text[:200]}... [truncated]")
                    else:
                        print(f"-> {output_text}")
            
            # 3. Append the tool execution results back to the conversation as the "user"
            messages.append(types.Content(role="user", parts=function_results))
        else:
            # 4. If there are no function calls, the agent has its final answer! 
            print("Final response:")
            print(response.text)
            
            # BREAK OUT OF THE LOOP
            return
        
    # 5. If we hit 20 iterations without a final answer, kill it.
    print("Error: Agent reached maximum iterations without completing the task.")
    sys.exit(1)

if __name__ == "__main__":
    main()