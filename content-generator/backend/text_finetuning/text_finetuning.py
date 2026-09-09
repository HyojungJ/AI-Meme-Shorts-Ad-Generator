import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer
import argparse
import os


def setup_model_and_tokenizer(model_id):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        quantization_config=bnb_config, 
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    return model, tokenizer


def formatting_prompts_func(example):
    output_texts = []
    
    if isinstance(example['instruction'], str):
        text = f"### 지시:\n{example['instruction']}\n\n### 입력:\n{example['input']}\n\n### 답변:\n{example['output']}<|end_of_text|>"
        return text
    else:
        for i in range(len(example['instruction'])):
            instruction = example['instruction'][i] if i < len(example['instruction']) else ""
            input_text = example['input'][i] if i < len(example['input']) else ""
            output_text = example['output'][i] if i < len(example['output']) else ""
            
            text = f"### 지시:\n{instruction}\n\n### 입력:\n{input_text}\n\n### 답변:\n{output_text}<|end_of_text|>"
            output_texts.append(text)
        
        return output_texts


def setup_lora_config():
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    return peft_config


def setup_training_args(output_dir="./eeve-persona-results", 
                       batch_size=4, 
                       gradient_accumulation_steps=4,
                       learning_rate=2e-4,
                       num_epochs=3,
                       save_steps=100):
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate, 
        logging_steps=10,
        num_train_epochs=num_epochs,
        save_strategy="steps",
        save_steps=save_steps,
        lr_scheduler_type="cosine",
        optim="paged_adamw_32bit",
        fp16=False,
        bf16=False,
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        gradient_checkpointing=True,
    )
    
    return training_args


def load_training_dataset(dataset_path):
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"데이터셋 파일을 찾을 수 없습니다: {dataset_path}")
    
    dataset = load_dataset("json", data_files=dataset_path, split="train")
    
    if len(dataset) > 0:
        sample = dataset[0]
        required_fields = ['instruction', 'input', 'output']
        missing_fields = [field for field in required_fields if field not in sample]
        if missing_fields:
            raise ValueError(f"필수 필드가 누락되었습니다: {missing_fields}")
    
    return dataset


def train_model(model, dataset, peft_config, training_args):
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        formatting_func=formatting_prompts_func,
        args=training_args,
    )
    
    trainer.train()
    return trainer


def save_model(trainer, save_path="./final_persona_model"):
    os.makedirs(save_path, exist_ok=True)
    trainer.model.save_pretrained(save_path)


def main():
    parser = argparse.ArgumentParser(description="텍스트 파인튜닝 스크립트")
    parser.add_argument("--model_id", default="yanolja/YanoljaNEXT-EEVE-Instruct-10.8B", 
                       help="사용할 모델 ID")
    parser.add_argument("--dataset_path", default="text_training_data.jsonl", 
                       help="학습 데이터셋 경로")
    parser.add_argument("--output_dir", default="./eeve-persona-results", 
                       help="학습 결과 저장 디렉토리")
    parser.add_argument("--final_model_path", default="./final_persona_model", 
                       help="최종 모델 저장 경로")
    parser.add_argument("--batch_size", type=int, default=2, 
                       help="배치 크기")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, 
                       help="그래디언트 누적 스텝")
    parser.add_argument("--learning_rate", type=float, default=2e-4, 
                       help="학습률")
    parser.add_argument("--num_epochs", type=int, default=3, 
                       help="학습 에포크 수")
    parser.add_argument("--save_steps", type=int, default=100, 
                       help="모델 저장 간격")
    
    args = parser.parse_args()
    
    model, tokenizer = setup_model_and_tokenizer(args.model_id)
    dataset = load_training_dataset(args.dataset_path)
    peft_config = setup_lora_config()
    training_args = setup_training_args(
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        num_epochs=args.num_epochs,
        save_steps=args.save_steps
    )
    
    trainer = train_model(model, dataset, peft_config, training_args)
    save_model(trainer, args.final_model_path)
    
    return 0


if __name__ == "__main__":
    exit(main())