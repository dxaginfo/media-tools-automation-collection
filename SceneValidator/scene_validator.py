#!/usr/bin/env python3
"""
SceneValidator - Tool for validating scene composition and continuity

This tool analyzes video frames to ensure continuity and proper composition
between scenes using Google Cloud Vision API and Gemini API for analysis.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional

# Placeholder for Google Cloud Vision API
try:
    from google.cloud import vision
    from google.cloud.vision import types
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("Google Cloud Vision API not available. Install with: pip install google-cloud-vision")

# Placeholder for Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini API not available. Install with: pip install google-generativeai")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scene_validator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SceneValidator")

class SceneValidator:
    """Main class for validating scene composition and continuity."""
    
    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None):
        """Initialize the SceneValidator.
        
        Args:
            api_key: Gemini API key
            project_id: Google Cloud project ID
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        
        # Initialize Vision API client
        if VISION_AVAILABLE and self.project_id:
            self.vision_client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision API initialized successfully")
        else:
            self.vision_client = None
            logger.warning("Google Cloud Vision API not initialized")
            
        # Initialize Gemini API
        if GEMINI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro-vision')
            logger.info("Gemini API initialized successfully")
        else:
            self.gemini_model = None
            logger.warning("Gemini API not initialized")
    
    def analyze_frame(self, image_path: str) -> Dict[str, Any]:
        """Analyze a single frame using Vision API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing analysis results
        """
        if not self.vision_client:
            logger.error("Vision API client not initialized")
            return {"error": "Vision API client not initialized"}
        
        try:
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.vision_client.annotate_image({
                'image': image,
                'features': [
                    {'type_': vision.Feature.Type.OBJECT_LOCALIZATION},
                    {'type_': vision.Feature.Type.LABEL_DETECTION},
                    {'type_': vision.Feature.Type.IMAGE_PROPERTIES},
                ]
            })
            
            # Extract relevant information
            result = {
                "objects": [{
                    "name": obj.name,
                    "confidence": obj.score,
                    "bounding_box": [
                        {"x": vertex.x, "y": vertex.y}
                        for vertex in obj.bounding_poly.normalized_vertices
                    ]
                } for obj in response.localized_object_annotations],
                "labels": [{
                    "description": label.description,
                    "confidence": label.score
                } for label in response.label_annotations],
                "colors": [{
                    "color": [c.red, c.green, c.blue],
                    "score": color.score,
                    "pixel_fraction": color.pixel_fraction
                } for color in response.image_properties_annotation.dominant_colors.colors]
            }
            
            logger.info(f"Successfully analyzed frame: {image_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return {"error": str(e)}
    
    def compare_frames(self, frame1_analysis: Dict[str, Any], frame2_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two frames to check for continuity issues.
        
        Args:
            frame1_analysis: Analysis results of the first frame
            frame2_analysis: Analysis results of the second frame
            
        Returns:
            Dictionary containing comparison results and potential continuity issues
        """
        if "error" in frame1_analysis or "error" in frame2_analysis:
            return {"error": "Cannot compare frames due to analysis errors"}
        
        # Simple object comparison
        frame1_objects = {obj["name"]: obj for obj in frame1_analysis["objects"]}
        frame2_objects = {obj["name"]: obj for obj in frame2_analysis["objects"]}
        
        # Find missing and new objects
        missing_objects = [name for name in frame1_objects if name not in frame2_objects]
        new_objects = [name for name in frame2_objects if name not in frame1_objects]
        
        # Compare dominant colors
        color_difference = self._calculate_color_difference(
            frame1_analysis["colors"],
            frame2_analysis["colors"]
        )
        
        result = {
            "missing_objects": missing_objects,
            "new_objects": new_objects,
            "color_difference": color_difference,
            "continuity_score": self._calculate_continuity_score(
                len(missing_objects), len(new_objects), color_difference
            )
        }
        
        logger.info(f"Frames comparison completed. Continuity score: {result['continuity_score']}")
        return result
    
    def _calculate_color_difference(self, colors1: List[Dict], colors2: List[Dict]) -> float:
        """Calculate the difference between dominant colors of two frames."""
        if not colors1 or not colors2:
            return 1.0
        
        # Simplified color comparison - average difference of top 3 colors
        top_colors1 = colors1[:min(3, len(colors1))]
        top_colors2 = colors2[:min(3, len(colors2))]
        
        total_diff = 0
        count = 0
        
        for c1 in top_colors1:
            for c2 in top_colors2:
                r_diff = abs(c1["color"][0] - c2["color"][0])
                g_diff = abs(c1["color"][1] - c2["color"][1])
                b_diff = abs(c1["color"][2] - c2["color"][2])
                total_diff += (r_diff + g_diff + b_diff) / (3 * 255) * c1["score"] * c2["score"]
                count += 1
        
        return total_diff / max(1, count)
    
    def _calculate_continuity_score(self, missing_count: int, new_count: int, color_diff: float) -> float:
        """Calculate an overall continuity score."""
        # Normalize each component to a 0-1 scale (lower is better)
        normalized_missing = min(1.0, missing_count / 10)  # Assume 10+ objects is maximum issue
        normalized_new = min(1.0, new_count / 10)
        
        # Weight factors
        weights = {"missing": 0.4, "new": 0.3, "color": 0.3}
        
        # Calculate weighted score (0 = completely different, 1 = perfect continuity)
        score = 1.0 - (
            weights["missing"] * normalized_missing +
            weights["new"] * normalized_new +
            weights["color"] * color_diff
        )
        
        return max(0.0, min(1.0, score))
    
    def get_gemini_analysis(self, image_path: str) -> Dict[str, Any]:
        """Get Gemini API analysis of a scene for composition quality.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing Gemini's analysis
        """
        if not self.gemini_model:
            logger.error("Gemini API not initialized")
            return {"error": "Gemini API not initialized"}
        
        try:
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
            
            prompt = """
            Analyze this frame from a video and provide feedback on:
            1. Scene composition quality (rule of thirds, balance, framing)
            2. Lighting assessment
            3. Depth and perspective
            4. Potential continuity issues if this were part of a sequence
            5. Overall visual quality rating (1-10 scale)
            Provide your analysis in JSON format with these categories.
            """
            
            response = self.gemini_model.generate_content(
                [prompt, image_data]
            )
            
            # Extract JSON from response
            try:
                analysis = json.loads(response.text)
                logger.info(f"Successfully got Gemini analysis for: {image_path}")
                return analysis
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                logger.warning(f"Gemini did not return valid JSON. Using raw response.")
                return {"raw_analysis": response.text}
                
        except Exception as e:
            logger.error(f"Error getting Gemini analysis: {e}")
            return {"error": str(e)}

    def validate_scene_sequence(self, frame_paths: List[str]) -> Dict[str, Any]:
        """Validate a sequence of frames for continuity and composition.
        
        Args:
            frame_paths: List of paths to frame images in sequence
            
        Returns:
            Dictionary containing validation results
        """
        if len(frame_paths) < 2:
            return {"error": "Need at least 2 frames to validate a sequence"}
        
        # Analyze all frames
        frame_analyses = [self.analyze_frame(path) for path in frame_paths]
        
        # Compare consecutive frames
        comparisons = [
            self.compare_frames(frame_analyses[i], frame_analyses[i+1])
            for i in range(len(frame_analyses) - 1)
        ]
        
        # Get composition analysis for key frames (first, last, and any with low continuity)
        composition_analyses = {}
        composition_analyses["first"] = self.get_gemini_analysis(frame_paths[0])
        composition_analyses["last"] = self.get_gemini_analysis(frame_paths[-1])
        
        # Find frames with continuity issues
        problem_frames = []
        for i, comp in enumerate(comparisons):
            if "continuity_score" in comp and comp["continuity_score"] < 0.7:
                problem_frames.append(i+1)  # +1 because it's the second frame in comparison
                if len(problem_frames) < 3:  # Limit to analyzing max 3 problem frames
                    composition_analyses[f"problem_{i+1}"] = self.get_gemini_analysis(frame_paths[i+1])
        
        result = {
            "frame_count": len(frame_paths),
            "continuity_scores": [c.get("continuity_score", 0) for c in comparisons],
            "average_continuity": sum(c.get("continuity_score", 0) for c in comparisons) / max(1, len(comparisons)),
            "problem_frames": problem_frames,
            "composition_analyses": composition_analyses,
            "validation_summary": self._generate_validation_summary(
                comparisons, composition_analyses, problem_frames
            )
        }
        
        logger.info(f"Completed validation of {len(frame_paths)} frames")
        return result
    
    def _generate_validation_summary(self, comparisons: List[Dict], composition_analyses: Dict, problem_frames: List[int]) -> Dict:
        """Generate a summary of the validation results."""
        avg_continuity = sum(c.get("continuity_score", 0) for c in comparisons) / max(1, len(comparisons))
        
        first_frame_quality = 0
        if "first" in composition_analyses and "overall_rating" in composition_analyses["first"]:
            try:
                first_frame_quality = float(composition_analyses["first"]["overall_rating"])
            except (ValueError, TypeError):
                first_frame_quality = 0
        
        last_frame_quality = 0
        if "last" in composition_analyses and "overall_rating" in composition_analyses["last"]:
            try:
                last_frame_quality = float(composition_analyses["last"]["overall_rating"])
            except (ValueError, TypeError):
                last_frame_quality = 0
        
        # Overall scene quality metric
        scene_quality = (avg_continuity * 0.6) + ((first_frame_quality + last_frame_quality) / 20) * 0.4
        
        return {
            "overall_continuity": avg_continuity,
            "scene_quality": scene_quality,
            "issue_count": len(problem_frames),
            "recommendations": self._generate_recommendations(comparisons, composition_analyses, problem_frames)
        }
    
    def _generate_recommendations(self, comparisons: List[Dict], composition_analyses: Dict, problem_frames: List[int]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Check for low continuity
        if problem_frames:
            frames_str = ", ".join(str(f) for f in problem_frames[:3])
            if len(problem_frames) > 3:
                frames_str += f" and {len(problem_frames) - 3} more"
            recommendations.append(f"Review continuity in frames {frames_str}")
        
        # Check composition issues
        composition_issues = {}
        for key, analysis in composition_analyses.items():
            if "composition_quality" in analysis:
                issues = analysis.get("composition_issues", [])
                for issue in issues:
                    if issue not in composition_issues:
                        composition_issues[issue] = 0
                    composition_issues[issue] += 1
        
        for issue, count in composition_issues.items():
            if count >= 2:  # If issue appears in multiple frames
                recommendations.append(f"Fix {issue} composition issue")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Scene appears to have good continuity and composition")
        
        return recommendations

def main():
    """Main function to run the tool from command line."""
    parser = argparse.ArgumentParser(description="SceneValidator: Validate scene composition and continuity")
    parser.add_argument("--frames", nargs="+", required=True, help="Paths to frame images in sequence")
    parser.add_argument("--output", help="Path to output JSON file")
    parser.add_argument("--api-key", help="Gemini API key")
    parser.add_argument("--project-id", help="Google Cloud project ID")
    args = parser.parse_args()
    
    validator = SceneValidator(api_key=args.api_key, project_id=args.project_id)
    result = validator.validate_scene_sequence(args.frames)
    
    # Pretty print to console
    print(json.dumps(result, indent=2))
    
    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
