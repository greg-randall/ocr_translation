#!/usr/bin/env python3
"""
clean.py - Script to clean OCR-generated markdown using AI models
"""

import os
import argparse
from pathlib import Path

# Import from utility module
import utils


# Default prompts for cleaning
CLEANING_SYSTEM_PROMPT = "You are a deliberate and careful editor of old French"
CLEANING_USER_PROMPT = (
    "I created the following French 1500s text with OCR, and it might have missed "
    "some characters or made minor mistakes. Correct anything you see wrong, and "
    "respond with only the corrected information. Maintain the markdown formatting "
    "of the original."
)

# Available models
MODELS = ["openai:gpt-4o", "anthropic:claude-3-5-sonnet-20240620"]


def clean_markdown_with_llm(
    input_path,
    output_path=None,
    model="openai:gpt-4o",
    system_prompt=CLEANING_SYSTEM_PROMPT,
    user_prompt=CLEANING_USER_PROMPT,
    temperature=0.75,
):
    """
    Clean a markdown file using an LLM.

    Args:
        input_path (str): Path to the input markdown file
        output_path (str, optional): Path to save the cleaned markdown file.
                                    If None, creates an appropriate path.
        model (str, optional): LLM model to use. Defaults to "openai:gpt-4o".
        system_prompt (str, optional): Custom system prompt. Defaults to CLEANING_SYSTEM_PROMPT.
        user_prompt (str, optional): Custom user prompt. Defaults to CLEANING_USER_PROMPT.
        temperature (float, optional): Temperature for LLM generation. Defaults to 0.75.

    Returns:
        dict: Results dictionary with paths and success status
    """
    results = {
        "success": False,
        "input_path": input_path,
        "output_path": output_path,
        "cleaned_text": None,
    }

    # Read the markdown file
    markdown_text = utils.read_markdown(input_path)
    if markdown_text is None:
        return results

    # Generate appropriate output path if none provided
    if output_path is None:
        output_dir = "cleaned"
        output_path = utils.get_output_path(input_path, output_dir)

    results["output_path"] = output_path

    try:
        # Create AI client
        ai_client = utils.TextAI(model=model)

        # Call the LLM to clean the text
        print(f"Cleaning markdown using {model}...")
        cleaned_text = ai_client.call(
            system_prompt, user_prompt, markdown_text, temperature
        )
        results["cleaned_text"] = cleaned_text

        # Save the cleaned text
        if utils.save_markdown(cleaned_text, output_path):
            results["success"] = True

    except Exception as e:
        print(f"Error during cleaning process: {e}")

    return results


def batch_clean_directory(
    input_dir,
    output_dir="cleaned",
    file_pattern="*.md",
    model="openai:gpt-4o",
    system_prompt=CLEANING_SYSTEM_PROMPT,
    user_prompt=CLEANING_USER_PROMPT,
    temperature=0.75,
):
    """
    Clean all markdown files in a directory.

    Args:
        input_dir (str): Directory containing markdown files to clean
        output_dir (str, optional): Directory to save cleaned files.
        file_pattern (str, optional): Pattern to match files. Defaults to "*.md".
        model (str, optional): LLM model to use. Defaults to openai:gpt-4o.
        system_prompt (str, optional): Custom system prompt. Defaults to CLEANING_SYSTEM_PROMPT.
        user_prompt (str, optional): Custom user prompt. Defaults to CLEANING_USER_PROMPT.
        temperature (float, optional): Temperature for LLM generation. Defaults to 0.75.

    Returns:
        list: List of results dictionaries for each file
    """
    results = []

    # Get all markdown files in the input directory
    markdown_files = utils.find_files(input_dir, file_pattern)

    if not markdown_files:
        print(f"No files matching '{file_pattern}' found in {input_dir}")
        return results

    print(f"Found {len(markdown_files)} markdown files to clean")

    # Create output directory if it doesn't exist
    utils.ensure_dir(output_dir)

    # Process each file
    for file_path in markdown_files:
        # Construct output path in the output directory
        rel_path = (
            file_path.relative_to(Path(input_dir))
            if Path(input_dir) in file_path.parents
            else file_path.name
        )
        output_path = Path(output_dir) / rel_path

        # Clean the file
        print(f"Cleaning {file_path}...")
        file_result = clean_markdown_with_llm(
            str(file_path),
            str(output_path),
            model,
            system_prompt,
            user_prompt,
            temperature,
        )

        results.append(file_result)

    # Print summary
    utils.print_batch_summary(results)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean OCR-generated markdown files using AI"
    )

    # Input and output options
    parser.add_argument("input", help="Input markdown file or directory")
    parser.add_argument(
        "--output",
        "-o",
        default="cleaned",
        help="Output markdown file or directory (default: 'cleaned' directory)",
    )
    parser.add_argument(
        "--batch",
        "-b",
        action="store_true",
        help="Process all markdown files in input directory",
    )
    parser.add_argument(
        "--pattern",
        "-p",
        default="*.md",
        help="File pattern when using batch mode (default: *.md)",
    )

    # Model and prompt options
    parser.add_argument(
        "--model",
        "-m",
        default="openai:gpt-4o",
        choices=MODELS,
        help="AI model to use for cleaning",
    )
    parser.add_argument(
        "--system-prompt",
        "-s",
        default=CLEANING_SYSTEM_PROMPT,
        help="Custom system prompt for cleaning",
    )
    parser.add_argument(
        "--user-prompt",
        "-u",
        default=CLEANING_USER_PROMPT,
        help="Custom user prompt for cleaning",
    )
    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=0.75,
        help="Temperature for LLM generation (0.0-1.0)",
    )

    args = parser.parse_args()

    # Determine if we're processing a single file or a directory
    if args.batch or os.path.isdir(args.input):
        batch_clean_directory(
            args.input,
            args.output,
            args.pattern,
            args.model,
            args.system_prompt,
            args.user_prompt,
            args.temperature,
        )
    else:
        result = clean_markdown_with_llm(
            args.input,
            args.output,
            args.model,
            args.system_prompt,
            args.user_prompt,
            args.temperature,
        )

        if result["success"]:
            print(f"Successfully cleaned {args.input}")
            print(f"Cleaned markdown saved to {result['output_path']}")
        else:
            print(f"Failed to clean {args.input}")
