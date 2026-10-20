# Escape the Chapter · Gemma + Streamlit

A server-side Python version of the SmartWorld classroom quiz. Students paste a passage or upload a page; the app creates Easy, Medium, and Hard questions using Gemma through Google's Gemini API. The Google key is read only by Python on the server and is never shown in the student interface.

## Run it on Windows

1. Install Python 3.10 or newer.
2. Open PowerShell in this folder.
3. Install the packages:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements.txt
   ```

4. Create a Google AI Studio API key. The app uses the hosted Gemma model `gemma-4-26b-a4b-it` through Google's Gemini API.
5. Copy `.streamlit\secrets.toml.example` to `.streamlit\secrets.toml`, open the new file, and replace the example value with your key:

   ```toml
   GEMINI_API_KEY = "your-real-key-goes-here"
   ```

   Keep `secrets.toml` private. It is excluded by `.gitignore`; do not put the key in `app.py`, HTML, a student form, or a public repository.

6. Start the app:

   ```powershell
   py -m streamlit run app.py
   ```

Streamlit opens the app in your browser. The Biology and History samples work without a key. A key is required when students submit their own passage or a textbook image.

## Uploads and quiz grounding

- Paste text or upload `.txt`, `.md`, `.csv`, a text-based `.pdf`, or a `.png`, `.jpg`, `.jpeg`, or `.webp` page image.
- Image uploads go to Gemma for reading. PDF text is extracted on the Python server. Scanned PDFs should be uploaded as page images.
- Text-passage responses are rejected if Gemma changes the source text. Every question also needs an evidence quote found in the supplied/transcribed passage.
- Starting score: 60. Each hint costs 20 points. The player starts with 3 lives. After the third wrong answer, the app prepares a new round for the same topic and carries the score and timer forward.
- A correct answer awards a randomly assigned fragment. The three fragments are shuffled at the final word gate. The player must enter the completed random word to finish.
- A hint-free three-question round adds 20 points to the saved bonus wallet. The wallet is preserved while the same Streamlit browser session is active.

## Deploy for students

For Streamlit Community Cloud, publish this folder from a private or public GitHub repository, choose `app.py` as the entry point, and put the key in the app's **Settings → Secrets** area instead of committing `secrets.toml`. Students use the hosted Streamlit URL; the API key remains on the server. If the app is public, use Google AI Studio quotas and billing limits appropriate for your class.

## Model selection

The default is `gemma-4-26b-a4b-it`. To use another Gemma model supported by the Gemini API, set `GEMMA_MODEL` in the server environment. Do not expose that setting as a student-facing field.
