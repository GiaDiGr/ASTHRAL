# Third-party assets

The Python reference modules retain their existing repository terms. No new project license is granted here.

* Pyodide 0.29.3: MPL-2.0; CPython and bundled wheels retain upstream licenses. Official distribution https://github.com/pyodide/pyodide and its included package metadata apply. Runtime bytes are pinned in runtime-lock.json.
* WebLLM 0.2.79 and Transformers.js 3.8.1: Apache-2.0; full license texts accompany this build. npm archives are integrity-pinned.
* Qwen2.5-0.5B-Instruct, Qwen3-4B and all-MiniLM-L6-v2: Apache-2.0 per the pinned model cards. Public model assets download only after explicit opt-in; weights are not committed.
* Vosk-browser 0.0.8 and vosk-model-small-en-us-0.15: Apache-2.0; CSP-safe browser initialization and synthetic file transcription have been exercised; physical microphone acceptance remains pending. Three legacy dynamic ABI wrappers are replaced by reviewed static wrappers without changing model weights; source is voice_csp_glue.js. prepare_voice.py verifies the reference model file hashes and npm package integrity.

Source model identifiers, revisions, sizes and SHA-256 hashes are recorded in src/models.json and src/voice-model.json. Browser MiniLM-L6 is a separate index from the Windows L12 model. The local corpus includes the original seven approved project/research sources and their provenance categories. Implementation criteria and research syntheses are not original guideline articles or independent clinical validation. Unreviewed translations and online publication metadata do not become clinical authority.

Six bundled WAV files are fully synthetic software-test fixtures, identified by src/test-audio/manifest.json hashes. They were generated locally with Piper en_US-ljspeech-high and eSpeak phonemes; the LJSpeech dataset model card describes the dataset as public domain. Piper ONNX model weights and the test generation toolchain are not redistributed in this application. Test utterances are not medical records and are not used to establish clinical validity.
