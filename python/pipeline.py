########################
# Libraries
########################

import sys
import json
from pathlib import Path

from llm_data_checker import read_df, df_checker_v2


########################
# Error handling
########################

def fail(msg):
    print(json.dumps({
        "status": "error",
        "message": msg
    }))
    sys.exit(1)  


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif hasattr(obj, "item"):  # numpy scalars
        return obj.item()
    else:
        return obj
    
########################
# Path setup
########################

BASE_DIR = Path(__file__).parent
FRAMEWORKS_DIR = BASE_DIR / "frameworks"


########################
# Argument parsing
########################

def parse_arguments():
    if len(sys.argv) != 4:
        fail("Expected 3 arguments: csv_path, provider, api_key")

    return {
        "csv_path": sys.argv[1],
        "provider": sys.argv[2],
        "api_key": sys.argv[3],
    }


########################
# Stats generation
########################

def gen_stats(csv_path):
    df = read_df(csv_path)

    print(f"[DEBUG] df type: {type(df)}", file=sys.stderr)

    if df is None:
        fail(f"Could not read CSV at: {csv_path}")

    # 🔥 enforce correct type
    import pandas as pd
    if not isinstance(df, pd.DataFrame):
        fail(f"Expected DataFrame, got {type(df)}")

    try:
        stats = df_checker_v2(df)
    except Exception as e:
        fail(f"df_checker_v2 failed: {str(e)}")

    print(f"[DEBUG] stats type: {type(stats)}", file=sys.stderr)

    if not isinstance(stats, dict):
        fail(f"Expected dict from df_checker_v2, got {type(stats)}")

    return stats


########################
# Prompt building
########################

def build_prompt(stats):
    system_template = (FRAMEWORKS_DIR / "prompt.txt").read_text()
    func_test_suite = (FRAMEWORKS_DIR / "func_test_suite.txt").read_text()
    function_format = (FRAMEWORKS_DIR / "function_format.txt").read_text()
    reasoning = (FRAMEWORKS_DIR / "reasoning.txt").read_text()
    helper_reg = (FRAMEWORKS_DIR / "helper_reg.txt").read_text()

    stats_str = json.dumps(make_json_safe(stats), indent=2)

    # DEBUG prints
    print("[DEBUG] prompt template loaded", file=sys.stderr)
    print("[DEBUG] func_test_suite length:", len(func_test_suite), file=sys.stderr)

    prompt = system_template.format(
        func_test_suite=func_test_suite,
        function_format=function_format,
        stats=stats_str,
        reasoning=reasoning,
        helper_reg=helper_reg
    )

    print("[DEBUG] final prompt length:", len(prompt), file=sys.stderr)

    return prompt


########################
# LLM Call
########################

def call_llm(prompt, provider, api_key):
    try:
        if provider == "cerebras":
            from cerebras.cloud.sdk import Cerebras
            client = Cerebras(api_key=api_key)

            completion = client.chat.completions.create(
                model="qwen-3-235b-a22b-instruct-2507",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "proceed"},
                ],
                max_completion_tokens=8192,
                temperature=0.0,
            )

            return completion.choices[0].message.content

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "proceed"},
                ],
                max_tokens=8192,
                temperature=0.0,
            )

            return completion.choices[0].message.content

        else:
            fail(f"Unknown provider: {provider}")

    except Exception as e:
        fail(f"LLM call failed: {str(e)}")


########################
# Output Parser
########################

def parse_output(raw_output):
    if not raw_output:
        fail("Empty response from LLM")

    try:
        if "===== FUNC_TEST_SUITE =====" in raw_output:
            parts = raw_output.split("===== REASONING =====")
            reasoning_section = parts[1].strip()

            code_section = parts[0].split("===== FUNC_TEST_SUITE =====")[1].strip()
        else:
            # 🔥 fallback: assume whole thing is code
            code_section = raw_output.strip()
            reasoning_section = "No reasoning provided"

        code_section = code_section.replace("```", "")
        reasoning_section = reasoning_section.replace("```", "")

        return {
            "cleaning_code": code_section,
            "reasoning": reasoning_section
        }

    except Exception as e:
        fail(f"Output parsing failed: {str(e)}")

    if "===== REASONING =====" not in raw_output:
        fail("Missing REASONING marker")

    try:
        parts = raw_output.split("===== REASONING =====")
        reasoning_section = parts[1].strip()

        code_section = parts[0].split("===== FUNC_TEST_SUITE =====")[1].strip()

        # 🔥 remove stray markdown
        code_section = code_section.replace("```", "")
        reasoning_section = reasoning_section.replace("```", "")

        return {
            "cleaning_code": code_section,
            "reasoning": reasoning_section
        }

    except Exception as e:
        fail(f"Output parsing failed: {str(e)}")


########################
# Entry point
########################

if __name__ == "__main__":
    try:
        args = parse_arguments()
        stats = gen_stats(args["csv_path"])
        prompt = build_prompt(stats)
        raw_output = call_llm(prompt, args["provider"], args["api_key"])
        parsed = parse_output(raw_output)

        print(json.dumps({
            "status": "success",
            "cleaning_code": parsed["cleaning_code"],
            "reasoning": parsed["reasoning"]
        }))

    except Exception as e:
        fail(f"Unhandled error: {str(e)}")