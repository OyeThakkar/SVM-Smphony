"""
Web Interface for Pod Compiler

Flask-based web UI for uploading CPLs and generating ad pods.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
from pathlib import Path
import tempfile
import shutil

from .compiler import PodCompiler, PodCompilerError
from .pod_identity import PodIdentity

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['OUTPUT_FOLDER'] = './output'


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/compile', methods=['POST'])
def compile_pod():
    """API endpoint to compile a pod"""
    try:
        # Get form data
        theatre_id = request.form.get('theatre_id', '').strip()
        rating = request.form.get('rating', '')
        section = request.form.get('section', '')
        aspect = request.form.get('aspect', '')
        start_date = request.form.get('start_date', '')
        
        # Validate date format
        if not PodIdentity.validate_date_format(start_date):
            return jsonify({
                'success': False,
                'error': f'Invalid date format. Expected dd-mmm-yyyy (e.g., 06-Feb-2026)'
            }), 400
        
        # Get uploaded files
        if 'cpl_files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No CPL files uploaded'
            }), 400
        
        files = request.files.getlist('cpl_files')
        
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No CPL files provided'
            }), 400
        
        if len(files) > 20:
            return jsonify({
                'success': False,
                'error': f'Too many files ({len(files)}). Maximum is 20.'
            }), 400
        
        # Save uploaded files
        upload_dir = Path(app.config['UPLOAD_FOLDER']) / f'upload_{os.urandom(8).hex()}'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        cpl_files = []
        for i, file in enumerate(files):
            if file.filename:
                file_path = upload_dir / f'cpl_{i}_{file.filename}'
                file.save(str(file_path))
                cpl_files.append(str(file_path))
        
        # Compile pod
        compiler = PodCompiler()
        result = compiler.compile_pod(
            theatre_id=theatre_id,
            rating=rating,
            section=section,
            aspect=aspect,
            start_date=start_date,
            cpl_files=cpl_files,
            output_dir=app.config['OUTPUT_FOLDER']
        )
        
        # Clean up uploaded files
        shutil.rmtree(upload_dir, ignore_errors=True)
        
        return jsonify({
            'success': True,
            'pod_name': result['pod_name'],
            'pod_id': result['pod_id'],
            'output_dir': result['output_dir'],
            'cpl_count': result['cpl_count'],
            'asset_count': result['asset_count'],
            'warnings': result['validation_warnings']
        })
        
    except PodCompilerError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/api/validate-date', methods=['POST'])
def validate_date():
    """API endpoint to validate date format"""
    data = request.get_json()
    date_str = data.get('date', '')
    
    valid = PodIdentity.validate_date_format(date_str)
    
    return jsonify({
        'valid': valid,
        'date': date_str
    })


def main():
    """Run the web server"""
    print("=" * 70)
    print("SVN-Symphony Ad Pod Compiler - Web Interface")
    print("=" * 70)
    print(f"\nStarting server on http://localhost:5000")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
    print("\nPress Ctrl+C to stop\n")
    
    # Create output folder
    Path(app.config['OUTPUT_FOLDER']).mkdir(parents=True, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
