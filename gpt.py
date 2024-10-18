import os

def concatenate_files_in_directory(directory_path):
    giant_string = ""

    # Traverse the directory and its subdirectories
    for root, dirs, files in os.walk(directory_path):
        # Skip directories that start with a dot (.)
        if any(part.startswith('.') for part in root.split(os.sep)):
            print(f"Skipping directory: {root}")
            continue

        for file_name in files:
            # Skip image files
            if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')):
                print(f"Skipping image file: {file_name}")
                continue

            file_path = os.path.join(root, file_name)
            # Prepend the directory structure to the file name in the string
            relative_path = os.path.relpath(file_path, directory_path)
            print(f"Processing file: {relative_path}")
            giant_string += f"File: {relative_path}\n"
            try:
                # Append file contents to the giant string
                with open(file_path, 'r', encoding='utf-8') as file:
                    contents = file.read()
                    giant_string += contents + "\n\n"  # Add an extra newline for separation
            except Exception as e:
                # Handle exceptions for reading files
                print(f"Could not read file {file_path}: {e}")
    return giant_string

# Replace with the path of your directory
directory_path = "."

# Delete code.txt if it exists
output_file_path = "code.txt"
if os.path.exists(output_file_path):
    os.remove(output_file_path)
    print(f"{output_file_path} deleted.")

# Get the concatenated result string
result_string = concatenate_files_in_directory(directory_path)

# Save the result to a file named "code.txt"
if result_string.strip():  # Check if the string is not empty
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(result_string)
    print("Giant string saved to code.txt")
else:
    print("No files were processed, code.txt was not written.")

