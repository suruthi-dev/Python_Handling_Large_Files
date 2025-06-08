from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import os
import io

app = Flask(__name__)

# Example documents
DOCUMENTS = [
    {"id": 1, "name": "Document A"},
    {"id": 2, "name": "Document B"},
    {"id": 3, "name": "Document C"}
]

# Rows for each document
ROWS = {
    1: ["Value 1", "Value 2", "Value 3"],
    2: ["Value 4", "Value 5", "Value 6"],
    3: ["Value 7", "Value 8", "Value 9"]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/documents')
def get_documents():
    return jsonify(DOCUMENTS)

@app.route('/api/rows/<int:doc_id>')
def get_rows(doc_id):
    return jsonify(ROWS.get(doc_id, []))


UPLOAD_FOLDER = 'uploads'
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def split_pdf_by_max_size(file_path, max_chunk_size=CHUNK_SIZE):
    
    """
    This function splits a large PDF file into smaller PDF files.
    Each resulting file will be less than or equal to max_chunk_size bytes (10MB default).
    """
     # Open the original PDF file
    reader = PdfReader(file_path)  #  reader.pages contains all the pages of your PDF. If book.pdf has 100 pages, you can access reader.pages[0], reader.pages[1], ..., reader.pages[99].
    base_name, ext = os.path.splitext(file_path)
    chunk_files = []    # Create a list to store all the new chunk file names

    writer = PdfWriter()     # Create a writer to hold pages of the current chunk.
    current_size = 0
    chunk_index = 1   # To name parts like part1, part2, etc.

    def write_chunk(writer, chunk_index):
        chunk_name = f"{base_name}_part{chunk_index}{ext}"
        with open(chunk_name, 'wb') as f:
            writer.write(f)  # Save the current chunk (e.g., first 20 pages) to a real file on disk., Save real chunk
        chunk_files.append(os.path.basename(chunk_name))

    for i, page in enumerate(reader.pages): # i is the page number (0, 1, 2, ..., 99 if 100 pages)
        temp_writer = PdfWriter()
        temp_writer.add_page(page) # Add one page to the writer # Add the current page to the current chunk (writer) (this will actually write the pages)

        # Measure this page in isolation
        temp_buffer = io.BytesIO() # Create a memory stream to hold current chunk data (instead of saving to disk),  we check how big that chunk is using io.BytesIO().
        temp_writer.write(temp_buffer)  # Write current chunk to memory
        page_size = len(temp_buffer.getvalue())

        if current_size + page_size > max_chunk_size and writer.pages:
            # Write current chunk
            write_chunk(writer, chunk_index)
            chunk_index += 1
            writer = PdfWriter()
            current_size = 0

        writer.add_page(page) # else continue
        current_size += page_size

    if writer.pages:
        write_chunk(writer, chunk_index)

    return chunk_files


def split_file_by_size(file_path, max_chunk_size_mb=5):
   
    max_chunk_size = max_chunk_size_mb * 1024 * 1024   # Convert the max chunk size from MB to bytes, because files are counted in bytes.
    base_name, ext = os.path.splitext(file_path)
    chunk_files = []  # This list will store the names of all the smaller chunk files we create.

    with open(file_path, 'r', encoding='utf-8') as f: # Open the original file in read mode with utf-8 encoding (for text files).
        chunk_index = 1  # To number each chunk like chunk1, chunk2, etc.
        current_chunk = [] # This will hold all the lines for the current chunk.
        current_size = 0  # This keeps track of the current chunk size in bytes.

        header = f.readline() # Read the first line which is usually the header (like column names in CSV).
        current_chunk.append(header)  # Add the header to the current chunk so every chunk has the header.
        current_size += len(header.encode('utf-8'))  # Update the current size with the header size.

        # Now loop through the rest of the lines in the file.
        for line in f:
            encoded_line = line.encode('utf-8')  # Convert the line to bytes to find out how many bytes it takes.
            line_size = len(encoded_line)

            # Check if adding this line would exceed the max chunk size.
            if current_size + line_size > max_chunk_size:
                # If yes, then save the current chunk to a new file.
                chunk_name = f"{base_name}_chunk{chunk_index}{ext}"
                with open(chunk_name, 'w', encoding='utf-8') as chunk_file:
                    chunk_file.writelines(current_chunk) # Write all lines of the current chunk to the file
              
                # Keep track of this new chunk's filename.
                chunk_files.append(os.path.basename(chunk_name))
                chunk_index += 1              # Prepare for the next chunk:
                current_chunk = [header, line] # Start the new chunk with the header and the current line.
                current_size = len(header.encode('utf-8')) + line_size # Reset the current chunk size.
            else:
                # If adding the line does NOT exceed size, add line to current chunk.
                current_chunk.append(line)
                current_size += line_size
        
        # After finishing all lines, write the last chunk to file.
        if current_chunk:
            chunk_name = f"{base_name}_chunk{chunk_index}{ext}"
            with open(chunk_name, 'w', encoding='utf-8') as chunk_file:
                chunk_file.writelines(current_chunk)
            chunk_files.append(os.path.basename(chunk_name))

    return chunk_files  # Return the list of chunk filenames created.


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    file_size = os.path.getsize(file_path)

    chunk_files = []

    if filename.lower().endswith(('.csv', '.txt')) and file_size > CHUNK_SIZE:
        chunk_files = split_file_by_size(file_path, max_chunk_size_mb=10)
        os.remove(file_path)
        return jsonify({
            'message': f'Text file split into {len(chunk_files)} chunks.',
            'chunks': chunk_files
        }), 200

    elif filename.lower().endswith('.pdf') and file_size > CHUNK_SIZE:
        chunk_files = split_pdf_by_max_size(file_path, max_chunk_size=CHUNK_SIZE)
        os.remove(file_path)
        return jsonify({
            'message': f'PDF split into {len(chunk_files)} chunks (max 10MB each).',
            'chunks': chunk_files
        }), 200

    elif file_size > CHUNK_SIZE:
        filename_no_ext, ext = os.path.splitext(filename)
        chunk_num = 0
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                chunk_filename = f"{filename_no_ext}_part{str(chunk_num).zfill(4)}{ext}"
                chunk_path = os.path.join(UPLOAD_FOLDER, chunk_filename)
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunk_files.append(chunk_filename)
                chunk_num += 1
        os.remove(file_path)
        return jsonify({
            'message': f'Binary file split into {chunk_num} chunks (raw bytes).',
            'chunks': chunk_files
        }), 200

    else:
        return jsonify({'message': 'File is small. Saved without chunking.'}), 200

if __name__ == '__main__':
    app.run(debug=True)