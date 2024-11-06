from flask import Flask, request, render_template, flash, redirect, url_for
import whisper
import os
import subprocess

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necessário para usar flash messages

# Carrega o modelo Whisper mais preciso
model = whisper.load_model("small")

# Certifica-se de que a pasta de uploads existe
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def preprocess_audio(input_path, output_path):
    try:
        # Converte o áudio para WAV mono a 16kHz, se necessário
        command = [
            "ffmpeg", "-i", input_path, "-ac", "1", "-ar", "16000", output_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise Exception(result.stderr.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Erro no processamento de áudio: {e}")

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_audio():
    if 'audio_file' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for('upload_form'))
    
    audio_file = request.files['audio_file']
    
    if audio_file.filename == '':
        flash("Nenhum arquivo selecionado.", "error")
        return redirect(url_for('upload_form'))
    
    if not audio_file.filename.endswith(('.mp3', '.wav')):
        flash("Formato de arquivo não suportado. Use MP3 ou WAV.", "error")
        return redirect(url_for('upload_form'))
    
    # Salva o arquivo enviado
    input_audio_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
    processed_audio_path = os.path.join(UPLOAD_FOLDER, "processed_audio.wav")
    audio_file.save(input_audio_path)

    try:
        # Pré-processamento do áudio
        preprocess_audio(input_audio_path, processed_audio_path)

        # Realiza a transcrição do áudio com maior precisão
        result = model.transcribe(processed_audio_path, language="pt", temperature=0.1)
        
        # Exibe a transcrição ao usuário
        flash(f"Texto transcrito: {result['text']}", "success")
    except RuntimeError as e:
        flash(f"Ocorreu um erro durante a transcrição: {e}", "error")
    finally:
        # Exclui os arquivos após a transcrição
        os.remove(input_audio_path)
        os.remove(processed_audio_path)

    return redirect(url_for('upload_form'))

if __name__ == '__main__':
    app.run(debug=True)
