# ComfyUI Custom Nodes - Smell

This repository contains a collection of custom nodes for ComfyUI, designed to enhance functionality and provide additional tools for image processing, prompt management, and large model integration.

## Features

### 1. **Image Processing Nodes**
- **Image Chooser**: Preview and select images during workflow execution.
- **Image Pad**: Apply custom padding to images with edge or color fill.
- **Image Saver**: Batch save images to a specified directory with metadata support.
- **Aspect Ratio Adjuster**: Adjust images to the best aspect ratio and scale to a maximum length.

### 2. **Prompt Management Nodes**
- **Positive Prompt Nodes**: Create and manage positive prompts for various models like NovelAI and Hunyuan.
- **Negative Prompt Nodes**: Manage negative prompts with JSON-based storage.
- **Template Selector Nodes**: Select and add prompt templates dynamically.

### 3. **Large Model Integration**
- **Ollama Vision**: Generate detailed descriptions of images using large models.
- **Ollama Generate**: Generate text responses with advanced options like context and sampling methods.

### 4. **Utility Nodes**
- **Checkpoint Loader**: Load model checkpoints with metadata support.
- **Logic Nodes**: Perform logical operations and manage workflow conditions.

## Installation
1. Clone this repository into your ComfyUI `custom_nodes` directory:
   ```bash
   git clone https://github.com/your-repo/ComfyUI_Custom_Nodes_Smell.git
   ```
2. Restart ComfyUI to load the new nodes.

## Usage
- Add the nodes to your workflow in ComfyUI.
- Configure the node parameters as needed.
- Run the workflow to see the results.

## Contributing
Contributions are welcome! Feel free to submit issues or pull requests to improve the functionality or add new features.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
