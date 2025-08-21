from langgraph.graph import StateGraph
import yaml

def save_architecture(app: StateGraph, filename: str = "architecture.png"):
    # Lấy binary PNG từ graph
    png_bytes = app.get_graph().draw_mermaid_png()
    filename = f"../../../assets/{filename}"
    
    # Ghi ra file
    with open(filename, "wb") as f:
        f.write(png_bytes)
    
    print(f"Architecture saved as {filename}")

def read_yaml_file(file_path: str) -> dict:
    with open(file_path, "r") as f:
        return yaml.safe_load(f)