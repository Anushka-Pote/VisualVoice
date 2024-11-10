from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename
import os
from PIL import Image
from transformers import pipeline
from gtts import gTTS
import hashlib
import time  # Import time module for adding a delay

app = Flask(__name__)

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['AUDIO_FOLDER'] = 'static/audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit to 16 MB

# Create uploads and audio directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

# Initialize the image-to-text pipeline
image_to_text = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

@app.route('/', methods=['GET', 'POST'])
def index():
    caption = ''
    image_url = ''
    audio_url = ''
    
    if request.method == 'POST' and 'photo' in request.files:
        # Process the uploaded photo
        photo = request.files['photo']
        filename = secure_filename(photo.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)

        # Generate a unique hash for the image file
        image_hash = hash_image(filepath)

        # File paths for caption and audio based on the image hash
        caption_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_hash}_caption.txt")
        audio_file = os.path.join(app.config['AUDIO_FOLDER'], f"{image_hash}.mp3")
        
        # Check if caption and audio files already exist
        if os.path.exists(caption_file) and os.path.exists(audio_file):
            # Simulate processing delay
            time.sleep(3)  # Add a 3-second delay

            # Read the caption from file and set the URLs
            with open(caption_file, 'r') as f:
                caption = f.read()
            image_url = url_for('static', filename=f'uploads/{filename}')
            audio_url = url_for('static', filename=f'audio/{image_hash}.mp3')
        else:
            # Convert the image to RGB and resize for optimization
            image = Image.open(filepath).convert('RGB')
            image = image.resize((500, 500))

            # Generate caption
            captions = image_to_text(image)
            caption = captions[0]['generated_text']
            
            # Save the caption to a text file for future use
            with open(caption_file, 'w') as f:
                f.write(caption)
            
            # Set image URL for display
            image_url = url_for('static', filename=f'uploads/{filename}')

            # Convert caption to audio using gtts and save the audio file
            if caption:
                tts = gTTS(text=caption, lang='en')
                tts.save(audio_file)
                audio_url = url_for('static', filename=f'audio/{image_hash}.mp3')

    return render_template('index.html', caption=caption, image_url=image_url, audio_url=audio_url)

def hash_image(image_path):
    """Generate a hash for the image content to use as a unique file key."""
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()  # MD5 hash of the image file

if __name__ == '__main__':
    app.run(debug=True)
