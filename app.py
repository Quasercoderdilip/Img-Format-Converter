from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from PIL import Image
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'converted'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_image(input_path, output_path, output_format):
    """Convert an image to a specific format, handling transparency for JPG."""
    try:
        with Image.open(input_path) as img:
            print(f"Original image mode: {img.mode}")  # Debug: Check input image mode

            # Handle transparency for JPG/JPEG
            if output_format.lower() in ('jpg', 'jpeg'):
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB and fill transparency with white
                    if img.mode == 'P':
                        img = img.convert('RGBA')  # Convert palette-based to RGBA first
                    
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                        img = background
                    else:
                        img = img.convert('RGB')  # Fallback for other modes
                else:
                    img = img.convert('RGB')  # Ensure non-transparent images are in RGB

            # Format mapping
            format_map = {
                'jpg': 'JPEG',
                'jpeg': 'JPEG',
                'png': 'PNG',
                'webp': 'WEBP',
                'bmp': 'BMP',
                'tiff': 'TIFF',
                'gif': 'GIF',
                'ico': 'ICO'
            }

            print(f"Saving as {format_map[output_format.lower()]}")  # Debug: Verify output format
            img.save(output_path, format=format_map[output_format.lower()], quality=95)  # Added quality option
            return True

    except Exception as e:
        print(f"Error converting image: {str(e)}")  # Debug: Print full error
        return False
    
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser submits empty file
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)
            
            # Get selected formats from form
            output_formats = request.form.getlist('formats')
            
            # Convert to selected formats
            converted_files = []
            base_name = os.path.splitext(filename)[0]
            
            for fmt in output_formats:
                output_filename = f"{base_name}.{fmt}"
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
                
                if convert_image(input_path, output_path, fmt):
                    converted_files.append(output_filename)
            
            return render_template('results.html', 
                                 original=filename,
                                 converted_files=converted_files)
    
    return render_template('upload.html')

@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)