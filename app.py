from flask import Flask, request, render_template
import whisper
import os
import subprocess

app = Flask(__name__)

# Carrega o modelo Whisper mais preciso
model = whisper.load_model("medium")

# Certifica-se de que a pasta de uploads existe
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def preprocess_audio(input_path, output_path):
    # Converte o áudio para WAV mono a 16kHz, se necessário
    command = [
        "ffmpeg", "-i", input_path, "-ac", "1", "-ar", "16000", output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_audio():
    if 'audio_file' not in request.files:
        return "Nenhum arquivo enviado.", 400
    
    audio_file = request.files['audio_file']
    
    if audio_file.filename == '':
        return "Nenhum arquivo selecionado.", 400
    
    if not audio_file.filename.endswith(('.mp3', '.wav')):
        return "Formato de arquivo não suportado. Use MP3 ou WAV.", 400
    
    # Salva o arquivo enviado
    input_audio_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
    processed_audio_path = os.path.join(UPLOAD_FOLDER, "processed_audio.wav")
    audio_file.save(input_audio_path)

    # Pré-processamento do áudio
    preprocess_audio(input_audio_path, processed_audio_path)

    try:
        # Realiza a transcrição do áudio com maior precisão
        result = model.transcribe(processed_audio_path, language="pt", temperature=0.1)
    except Exception as e:
        return f"Ocorreu um erro durante a transcrição: {e}", 500
    finally:
        # Exclui os arquivos após a transcrição
        os.remove(input_audio_path)
        os.remove(processed_audio_path)

    return f"Texto transcrito: {result['text']}"

if __name__ == '__main__':
    app.run(debug=True)
