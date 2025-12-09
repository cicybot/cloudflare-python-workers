import os
def file_get_content(file_path: str) -> str:
    """Read content from a file and return it as a string."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()  # Read the entire content of the file
        return content
    except FileNotFoundError:
        return f"Error: The file at {file_path} was not found."
    except Exception as e:
        return f"Error: {str(e)}"

def file_put_content(file_path: str, content: str) -> None:
    """Write content to a file (overwrite if the file exists)."""
    try:
        with open(file_path, 'w') as file:
            file.write(content)  # Write the content to the file
        print(f"Content successfully written to {file_path}")
    except Exception as e:
        print(f"Error: {str(e)}")



def file_exists(file_path: str) -> bool:
    """Check if a file exists at the given path."""
    return os.path.isfile(file_path)