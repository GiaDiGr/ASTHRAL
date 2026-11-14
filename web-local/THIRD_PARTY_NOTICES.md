# Third-party assets

The Python reference modules retain their existing repository terms. No new project license is granted here.

* Pyodide 0.29.3: MPL-2.0; CPython and bundled wheels retain upstream licenses. Official distribution https://github.com/pyodide/pyodide and its included package metadata apply. Runtime bytes are pinned in runtime-lock.json.
* WebLLM 0.2.79 and Transformers.js 3.8.1: Apache-2.0; full license texts accompany this build. npm archives are integrity-pinned.
* Qwen2.5-0.5B-Instruct, Qwen3-4B and all-MiniLM-L6-v2: Apache-2.0 per the pinned model cards. Public model assets download only after explicit opt-in; weights are not committed.
* Vosk-browser 0.0.8 and vosk-model-small-en-us-0.15: Apache-2.0; offline voice is experimental and failed initialization in this review. prepare_voice.py verifies the reference model file hashes and npm package integrity.

Source model identifiers, revisions, sizes and SHA-256 hashes are recorded in src/models.json and src/voice-model.json. Browser MiniLM-L6 is a separate index from the Windows L12 model. Only project-authored implementation notes are bundled as the retrieval corpus; they are not clinical guidelines.
