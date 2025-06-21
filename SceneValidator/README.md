# SceneValidator

Tool for validating scene composition and continuity using Gemini API and Google Cloud Vision.

## Description

SceneValidator analyzes video frames to detect continuity issues between scenes and evaluate composition quality. It uses Google Cloud Vision API for object detection and scene analysis, combined with Google's Gemini API for advanced scene composition evaluation.

## Features

- Frame-by-frame analysis of scene composition
- Continuity tracking between consecutive frames
- Object tracking and detection
- Color palette and lighting analysis
- Composition quality scoring based on cinematography principles
- Detailed recommendations for improving scene quality

## Installation

```bash
# Clone the repository
git clone https://github.com/dxaginfo/media-tools-automation-collection.git
cd media-tools-automation-collection/SceneValidator

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a config.json file based on the provided config_template.json:

```json
{
  "api_keys": {
    "gemini": "YOUR_GEMINI_API_KEY",
    "google_cloud": "YOUR_GOOGLE_CLOUD_API_KEY"
  },
  "google_cloud_project": "YOUR_GOOGLE_CLOUD_PROJECT_ID"
}
```

## Usage

```bash
# Basic usage with frame images
python scene_validator.py --frames frame001.jpg frame002.jpg frame003.jpg

# Save results to a file
python scene_validator.py --frames frame*.jpg --output results.json

# Specify API keys directly
python scene_validator.py --frames frame*.jpg --api-key YOUR_GEMINI_API_KEY --project-id YOUR_GCP_PROJECT_ID
```

## API Integration

The tool can be integrated with other applications through its Python API:

```python
from scene_validator import SceneValidator

# Initialize the validator
validator = SceneValidator(api_key="YOUR_GEMINI_API_KEY", project_id="YOUR_GCP_PROJECT_ID")

# Validate a sequence of frames
frame_paths = ["frame001.jpg", "frame002.jpg", "frame003.jpg"]
results = validator.validate_scene_sequence(frame_paths)

# Print validation summary
print(results["validation_summary"])
```

## Integration with Other Tools

- **StoryboardGen**: Validate storyboards against actual scene implementations
- **ContinuityTracker**: Detailed continuity analysis across multiple scenes
- **EnvironmentTagger**: Combine with environment tagging for contextual validation

## Dependencies

- google-cloud-vision
- google-generativeai
- Pillow

## License

MIT
