"""
vLLM Inference Server for Scenario Generation

RunPod Serverless compatible handler.
Loads fine-tuned LoRA adapter and serves scenario generation requests.
"""

import json
import os
import re

# Try importing vLLM (may not be available locally)
try:
    from vllm import LLM, SamplingParams
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False


def extract_json_from_response(text: str) -> dict | None:
    """Extract JSON from model response."""
    # Method 1: ```json code block
    code_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # Method 2: Find matching braces
    start_idx = text.find('{')
    if start_idx == -1:
        return None

    depth = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start_idx:i+1])
                except json.JSONDecodeError:
                    return None
    return None


class ScenarioGenerator:
    """Scenario generation using vLLM with LoRA adapter."""

    def __init__(
        self,
        model_path: str,
        lora_path: str | None = None,
        gpu_memory_utilization: float = 0.9,
    ):
        if not VLLM_AVAILABLE:
            raise RuntimeError("vLLM not available. Install with: pip install vllm")

        self.llm = LLM(
            model=model_path,
            enable_lora=lora_path is not None,
            max_lora_rank=64,
            tensor_parallel_size=1,
            gpu_memory_utilization=gpu_memory_utilization,
            trust_remote_code=True,
        )

        self.lora_path = lora_path
        self.sampling_params = SamplingParams(
            temperature=0.7,
            top_p=0.9,
            max_tokens=2000,
            stop=["<|im_end|>"],
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 2,
    ) -> dict:
        """Generate scenario with retry on validation failure."""
        # Format prompt (ChatML format)
        full_prompt = (
            f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        for attempt in range(max_retries):
            # Generate
            if self.lora_path:
                from vllm.lora.request import LoRARequest
                lora_request = LoRARequest("scenario_lora", 1, self.lora_path)
                outputs = self.llm.generate(
                    [full_prompt],
                    self.sampling_params,
                    lora_request=lora_request,
                )
            else:
                outputs = self.llm.generate([full_prompt], self.sampling_params)

            response_text = outputs[0].outputs[0].text

            # Extract JSON (validation is done client-side)
            scenario = extract_json_from_response(response_text)
            if scenario:
                return {
                    "status": "success",
                    "scenario": scenario,
                    "raw_response": response_text,
                }
            else:
                last_error = "JSON extraction failed"

        return {
            "status": "error",
            "error": last_error,
            "raw_response": response_text if 'response_text' in locals() else None,
        }


# Global generator instance (for RunPod serverless)
_generator: ScenarioGenerator | None = None


def get_generator() -> ScenarioGenerator:
    """Get or create generator instance."""
    global _generator
    if _generator is None:
        model_path = os.environ.get("MODEL_PATH", "/models/base")
        lora_path = os.environ.get("LORA_PATH", "/models/lora_adapter")
        _generator = ScenarioGenerator(model_path, lora_path)
    return _generator


def handler(event: dict) -> dict:
    """
    RunPod Serverless Handler.

    Expected input:
    {
        "input": {
            "system_prompt": "...",
            "user_prompt": "...",
            "max_retries": 2  # optional
        }
    }
    """
    try:
        input_data = event.get("input", {})
        system_prompt = input_data.get("system_prompt", "")
        user_prompt = input_data.get("user_prompt", "")
        max_retries = input_data.get("max_retries", 2)

        if not user_prompt:
            return {"error": "user_prompt is required"}

        generator = get_generator()
        result = generator.generate(system_prompt, user_prompt, max_retries)

        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}


# FastAPI server for local testing
def create_app():
    """Create FastAPI app for local testing."""
    from fastapi import FastAPI
    from pydantic import BaseModel

    app = FastAPI(title="Scenario Generator")

    class GenerateRequest(BaseModel):
        system_prompt: str = ""
        user_prompt: str
        max_retries: int = 2

    @app.post("/generate")
    async def generate(request: GenerateRequest):
        return handler({"input": request.model_dump()})

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="Base model path")
    parser.add_argument("--lora-path", help="LoRA adapter path")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # Set environment variables for generator
    os.environ["MODEL_PATH"] = args.model_path
    if args.lora_path:
        os.environ["LORA_PATH"] = args.lora_path

    # Run FastAPI server
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
