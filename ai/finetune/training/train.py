"""
QLoRA Fine-tuning Script for Scenario Generation

Uses Unsloth for efficient 4-bit training on consumer GPUs.
Supports SKT A.X, Kakao Kanana, Mi:dm, and other compatible models.

Features:
- 4-bit QLoRA training with Unsloth
- NEFTune (Noisy Embeddings) for improved generation
- DoRA (Weight-Decomposed LoRA) option for better performance
- Gradient checkpointing for memory efficiency
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from dataclasses import dataclass
from transformers import TrainingArguments, Trainer, EarlyStoppingCallback

# Unsloth must be imported after torch
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    print("[Warning] Unsloth not available. Install with: pip install unsloth")

# Paths
FINETUNE_DIR = Path(__file__).parent.parent
DATA_DIR = FINETUNE_DIR / "data"
CONFIGS_DIR = Path(__file__).parent / "configs"
OUTPUTS_DIR = FINETUNE_DIR / "outputs"


def load_config(config_path: str) -> dict:
    """Load training config from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_dataset_from_jsonl(jsonl_path: Path, tokenizer, max_seq_length: int = 4096) -> Dataset:
    """Load and pre-tokenize chat-format dataset from JSONL file.

    Label masking: system/user 토큰은 -100으로 마스킹하여
    assistant 응답만 loss 계산에 포함.
    """
    all_input_ids = []
    all_attention_mask = []
    all_labels = []

    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                messages = record.get("messages", [])

                # 전체 대화 토크나이즈
                full_text = format_chat_messages(messages, tokenizer)
                encoded = tokenizer(
                    full_text,
                    truncation=True,
                    max_length=max_seq_length,
                    padding=False,
                )

                # assistant 응답 시작 위치 찾기: system+user만으로 토크나이즈
                non_assistant = [m for m in messages if m["role"] != "assistant"]
                prefix_text = tokenizer.apply_chat_template(
                    non_assistant, tokenize=False, add_generation_prompt=True,
                )
                prefix_ids = tokenizer(
                    prefix_text, truncation=True, max_length=max_seq_length,
                )["input_ids"]
                prefix_len = len(prefix_ids)

                # prefix 부분은 -100으로 마스킹 (loss 계산 제외)
                input_ids = encoded["input_ids"]
                labels = [-100] * min(prefix_len, len(input_ids)) + input_ids[prefix_len:]

                all_input_ids.append(input_ids)
                all_attention_mask.append(encoded["attention_mask"])
                all_labels.append(labels)

    return Dataset.from_dict({
        "input_ids": all_input_ids,
        "attention_mask": all_attention_mask,
        "labels": all_labels,
    })


def format_chat_messages(messages: list[dict], tokenizer) -> str:
    """Format messages using model's native chat template."""
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )


def load_datasets(data_dir: Path, tokenizer, max_seq_length: int = 4096) -> tuple[Dataset, Dataset]:
    """Load train and validation datasets."""
    train_path = data_dir / "splits" / "train.jsonl"
    val_path = data_dir / "splits" / "val.jsonl"

    if not train_path.exists():
        curated_dir = data_dir / "curated"
        if curated_dir.exists():
            jsonl_files = list(curated_dir.glob("*.jsonl"))
            if jsonl_files:
                train_ds = load_dataset_from_jsonl(jsonl_files[0], tokenizer, max_seq_length)
                val_ds = train_ds.select(range(min(10, len(train_ds))))
                return train_ds, val_ds

        raise FileNotFoundError(f"No training data found in {data_dir}")

    train_ds = load_dataset_from_jsonl(train_path, tokenizer, max_seq_length)
    val_ds = load_dataset_from_jsonl(val_path, tokenizer, max_seq_length)

    return train_ds, val_ds


def setup_wandb(config: dict, run_name: str):
    """Initialize Weights & Biases logging."""
    if not config.get("use_wandb", False):
        return

    try:
        import wandb
        wandb.init(
            project=config.get("wandb_project", "scenario-finetuning"),
            name=run_name,
            config=config,
        )
    except ImportError:
        print("[Warning] wandb not installed. Skipping W&B logging.")


def train(
    config_path: str,
    data_dir: str | None = None,
    output_dir: str | None = None,
    resume_from: str | None = None,
):
    """Main training function."""
    if not UNSLOTH_AVAILABLE:
        raise RuntimeError("Unsloth is required for training. Install with: pip install unsloth")

    # Load config
    config = load_config(config_path)
    print(f"[1/6] Loaded config: {config_path}")

    # Setup paths
    data_path = Path(data_dir) if data_dir else DATA_DIR
    if output_dir:
        out_path = Path(output_dir)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUTS_DIR / f"{config['model_name'].split('/')[-1]}_{timestamp}"

    out_path.mkdir(parents=True, exist_ok=True)
    print(f"[2/6] Output directory: {out_path}")

    # Setup W&B
    run_name = out_path.name
    setup_wandb(config, run_name)

    # Load model with Unsloth (4-bit quantization)
    print(f"[3/6] Loading model: {config['model_name']}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["model_name"],
        max_seq_length=config.get("max_seq_length", 4096),
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )

    # Add LoRA adapters (with optional DoRA)
    peft_kwargs = {
        "r": config.get("lora_r", 16),
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj"],
        "lora_alpha": config.get("lora_alpha", 32),
        "lora_dropout": config.get("lora_dropout", 0.05),
        "bias": "none",
        "use_gradient_checkpointing": "unsloth",
        "random_state": 42,
    }
    if config.get("use_dora"):
        peft_kwargs["use_dora"] = True
        print("  DoRA enabled")
    model = FastLanguageModel.get_peft_model(model, **peft_kwargs)

    # Load datasets
    print(f"[4/6] Loading datasets from: {data_path}")
    max_seq_length = config.get("max_seq_length", 4096)
    train_ds, val_ds = load_datasets(data_path, tokenizer, max_seq_length)
    print(f"  Train: {len(train_ds)} samples, Val: {len(val_ds)} samples")

    # NEFTune: add noise to embeddings
    if config.get("use_neftune"):
        alpha = config.get("neftune_noise_alpha", 5)
        model.config.neftune_noise_alpha = alpha
        print(f"  NEFTune enabled (alpha={alpha})")

    # Training arguments (standard Trainer — avoids SFTTrainer logits issue with Unsloth)
    training_args = TrainingArguments(
        output_dir=str(out_path),
        per_device_train_batch_size=config.get("batch_size", 2),
        gradient_accumulation_steps=config.get("grad_accum", 4),
        warmup_ratio=config.get("warmup_ratio", 0.1),
        num_train_epochs=config.get("epochs", 3),
        learning_rate=config.get("learning_rate", 2e-4),
        weight_decay=config.get("weight_decay", 0.01),
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="adamw_8bit",
        seed=42,
        save_strategy="steps",
        save_steps=config.get("save_steps", 100),
        eval_strategy="steps",
        eval_steps=config.get("eval_steps", 50),
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="wandb" if config.get("use_wandb") else "none",
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )

    # Create trainer
    print("[5/6] Starting training...")
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id

    @dataclass
    class PadCollator:
        """Pad variable-length sequences to max length in batch."""
        pad_token_id: int = pad_id

        def __call__(self, features):
            max_len = max(len(f["input_ids"]) for f in features)
            batch = {"input_ids": [], "attention_mask": [], "labels": []}
            for f in features:
                pad_len = max_len - len(f["input_ids"])
                batch["input_ids"].append(f["input_ids"] + [self.pad_token_id] * pad_len)
                batch["attention_mask"].append(f["attention_mask"] + [0] * pad_len)
                batch["labels"].append(f["labels"] + [-100] * pad_len)
            return {k: torch.tensor(v) for k, v in batch.items()}

    early_stopping_patience = config.get("early_stopping_patience", 3)
    print(f"  Early stopping enabled (patience={early_stopping_patience})")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=PadCollator(),
        callbacks=[EarlyStoppingCallback(early_stopping_patience=early_stopping_patience)],
    )

    # Resume from checkpoint if specified
    if resume_from:
        trainer.train(resume_from_checkpoint=resume_from)
    else:
        trainer.train()

    # Save model
    print("[6/6] Saving model...")
    lora_path = out_path / "lora_adapter"
    model.save_pretrained(lora_path)
    tokenizer.save_pretrained(lora_path)

    # Save training info
    info = {
        "config": config,
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "output_dir": str(out_path),
        "lora_path": str(lora_path),
        "completed_at": datetime.now().isoformat(),
    }
    with open(out_path / "training_info.json", "w") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print(f"\nTraining complete!")
    print(f"  LoRA adapter saved to: {lora_path}")
    print(f"  Training info saved to: {out_path / 'training_info.json'}")

    return str(lora_path)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune scenario generation model")
    parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="Path to config YAML file (e.g., configs/skt_ax_7b.yaml)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Path to data directory (default: finetune/data)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Path to output directory"
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Path to checkpoint to resume from"
    )

    args = parser.parse_args()

    # Resolve config path
    config_path = args.config
    if not os.path.exists(config_path):
        config_path = str(CONFIGS_DIR / args.config)

    train(
        config_path=config_path,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        resume_from=args.resume,
    )


if __name__ == "__main__":
    main()
