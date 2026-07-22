import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM


class QwenEngine:

    def __init__(self, model_path=None):

        # ==========================================================
        # Device Selection
        # ==========================================================

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"\nUsing Device : {self.device}")

        # ==========================================================
        # Model Path
        # ==========================================================

        if model_path is None:
            project_root = Path(__file__).resolve().parent.parent
            model_path = project_root / "qwen2.5-coder-7b"

        self.model_path = str(model_path)

        print(f"Loading Model From : {self.model_path}")

        # ==========================================================
        # Load Tokenizer
        # ==========================================================

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True,
            trust_remote_code=True
        )

        # ==========================================================
        # Data Type
        # ==========================================================

        torch_dtype = (
            torch.float16
            if self.device == "cuda"
            else torch.float32
        )
        # ==========================================================
        # Load Model
        # ==========================================================

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            local_files_only=True,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )

        self.model.eval()

        print("\nQwen Loaded Successfully!")

    # ==========================================================
    # Generate Response
    # ==========================================================

    def generate(
        self,
        prompt,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.95,
        do_sample=True,
        repetition_penalty=1.05,
    ):

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert software engineer. "
                    "Always follow the user's instructions exactly. "
                    "Return only the requested output."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True
        ).to(self.device)

        generate_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "repetition_penalty": repetition_penalty,
            "pad_token_id": self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }

        if do_sample:
            generate_kwargs["temperature"] = temperature
            generate_kwargs["top_p"] = top_p

        try:

            with torch.inference_mode():

                outputs = self.model.generate(
                    **inputs,
                    **generate_kwargs
                )

            generated = outputs[0][inputs.input_ids.shape[1]:]

            response = self.tokenizer.decode(
                generated,
                skip_special_tokens=True
            )

            return response.strip()

        except torch.cuda.OutOfMemoryError:

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            print("\nCUDA Out Of Memory!")

            return ""

        except Exception as e:

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            print("\nGeneration Error:")
            print(e)

            return ""

        finally:

            if "outputs" in locals():
                del outputs

            if "inputs" in locals():
                del inputs

            if torch.cuda.is_available():
                torch.cuda.empty_cache()