# Separately acquired local assets

The owner's existing integration remains `http://127.0.0.1:8891`, provider `ollama`, model `vigile-qwen3-4b:latest`. This work does not change the installed model, fine-tune it, restart/reconfigure Ollama, restore quarantined llama-server.exe, or alter Norton.

The existing pinned weight is Qwen3-4B-Instruct-2507 Q4_K_M GGUF, 2,497,280,448 bytes, SHA-256 `8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc`. Recorded source: `https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF/resolve/4edb920b6f14e3b9284d4502a6485103d72cde05/Qwen3-4B-Instruct-2507-Q4_K_M.gguf`. Obtain and review its terms separately; weights are not committed. Verify hash before import. No download is needed on the owner workstation.

For a new approved workstation, place the separate GGUF beside a copy of engine/Modelfile.example, start an approved loopback-only Ollama instance, and create the existing tag using that file. The example imports the model without training. Change only that workstation's local endpoint configuration if needed; do not assume a remote or cloud model is acceptable.

English speech uses `vosk-model-small-en-us-0.15` and Windows SAPI Microsoft David Desktop. The pinned URLs/archive sizes/hashes and model-file hashes remain in engine/vigile/voice_assets/models.json. Download/install separately and verify the manifest; do not include binary assets in Git. The astronaut portal exposes English only while legacy assets remain locally recoverable. Synthesized-speech recognition is a software smoke test, not microphone accuracy or human listening acceptance. Review every transcript before sending; aliases are limited to the assistant's leading name.
