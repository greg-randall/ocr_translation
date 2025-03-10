#!/usr/bin/env python3
"""
clean.py - Script to clean OCR-generated markdown using AI models
"""

import os
import argparse
from pathlib import Path
from typing import Any

# Import from utility module
import utils.utils as utils
from utils import file_handling


# Default values as constants
DEFAULT_OUTPUT_DIR = "cleaned"
DEFAULT_FILE_PATTERN = "*.md"
DEFAULT_MODEL = "openai:gpt-4o"
DEFAULT_TEMPERATURE = 0.75

# Default prompts for cleaning
CLEANING_SYSTEM_PROMPT = "You are a deliberate and careful editor of old French"
CLEANING_USER_PROMPT = """You will be given an OCR-generated transcription of the 16th-century French legal text **"Arrest mémorable du Parlement de Tolose"** by Jean de Coras, a detailed account of the Martin Guerre impostor case. This OCR transcription contains transcription errors such as incorrect character recognition, misplaced punctuation, and spacing mistakes.
**Your task is to:**

1. **Correct all transcription errors**, ensuring accuracy in spelling, punctuation, capitalization, and spacing.
2. **Preserve the original 16th-century French style and vocabulary**, maintaining archaic language and legal terms as faithfully as possible.
3. **Pay particular attention to annotations**, which often contain classical references (e.g., Homer, Virgil, Cicero, and biblical passages), ensuring these are accurately transcribed and coherent in the context of the overall narrative.
4. Note that the annotations are often referenced through out the text with single letters. These single letters are not mistakes if they line up with an annotation.
5. **Retain original formatting** (such as headings, numbered annotations, and paragraph structure) wherever possible.
6. Respond with absolutely nothing except the edited text. Do not make any comments.

Begin now.
"""

# Available models
MODELS = ["openai:gpt-4o", "anthropic:claude-3-5-sonnet-20240620"]


def clean_markdown_with_llm(
    input_path: str,
    output_path: str | None = None,
    model: str = DEFAULT_MODEL,
    system_prompt: str = CLEANING_SYSTEM_PROMPT,
    user_prompt: str = CLEANING_USER_PROMPT,
    temperature: float = DEFAULT_TEMPERATURE,
) -> dict[str, bool | str | None]:
    """
    Clean a markdown file using an LLM.

    Args:
        input_path: Path to the input markdown file
        output_path: Path to save the cleaned markdown file.
                     If None, creates an appropriate path.
        model: LLM model to use
        system_prompt: Custom system prompt
        user_prompt: Custom user prompt
        temperature: Temperature for LLM generation

    Returns:
        dict: Results dictionary with paths and success status
    """
    results: dict[str, bool | str | None] = {
        "success": False,
        "input_path": input_path,
        "output_path": output_path,
        "cleaned_text": None,
    }

    # Read the markdown file
    markdown_text = file_handling.read_markdown(input_path)
    if markdown_text is None:
        return results

    # Generate appropriate output path if none provided
    if output_path is None:
        output_path = file_handling.get_output_path(input_path, DEFAULT_OUTPUT_DIR)

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
        if file_handling.save_markdown(cleaned_text, output_path):
            results["success"] = True

    except Exception as e:
        print(f"Error during cleaning process: {e}")

    return results


def batch_clean_directory(
    input_dir: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    file_pattern: str = DEFAULT_FILE_PATTERN,
    model: str = DEFAULT_MODEL,
    system_prompt: str = CLEANING_SYSTEM_PROMPT,
    user_prompt: str = CLEANING_USER_PROMPT,
    temperature: float = DEFAULT_TEMPERATURE,
) -> list[dict[str, bool | str | None]]:
    """
    Clean all markdown files in a directory.

    Args:
        input_dir: Directory containing markdown files to clean
        output_dir: Directory to save cleaned files
        file_pattern: Pattern to match files
        model: LLM model to use
        system_prompt: Custom system prompt
        user_prompt: Custom user prompt
        temperature: Temperature for LLM generation

    Returns:
        list: List of results dictionaries for each file
    """
    results: list[dict[str, bool | str | None]] = []

    # Get all markdown files in the input directory
    markdown_files = utils.find_files(input_dir, file_pattern)

    if not markdown_files:
        print(f"No files matching '{file_pattern}' found in {input_dir}")
        return results

    print(f"Found {len(markdown_files)} markdown files to clean")

    # Create output directory if it doesn't exist
    file_handling.ensure_dir(output_dir)

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
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output markdown file or directory (default: '{DEFAULT_OUTPUT_DIR}')",
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
        default=DEFAULT_FILE_PATTERN,
        help=f"File pattern when using batch mode (default: '{DEFAULT_FILE_PATTERN}')",
    )

    # Model and prompt options
    parser.add_argument(
        "--model",
        "-m",
        default=DEFAULT_MODEL,
        choices=MODELS,
        help=f"AI model to use for cleaning (default: '{DEFAULT_MODEL}')",
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
        default=DEFAULT_TEMPERATURE,
        help=f"Temperature for LLM generation (0.0-1.0) (default: {DEFAULT_TEMPERATURE})",
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
