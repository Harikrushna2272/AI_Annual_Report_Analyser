# Full code for PDF parsing using Docling with SmolDocling VLM (best for document parsing based on comparisons)
# SmolDocling is a compact VLM specialized for document conversion, outperforming much larger models in quality for this task.
# It supports DocTags output, which is preferred for structured formats.
# This code uses the Transformers framework for broader compatibility (works on CPU/GPU, not just Apple devices).
# For Apple devices with MPS, you can switch to SMOLDOCLING_MLX for faster inference.

# Installation (run in your environment):
# pip install docling
# For GPU support: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 (adjust for your CUDA version)
# For MLX on Apple: pip install mlx

import json
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel import vlm_model_specs

def parse_pdf_to_structured_format(pdf_path: str, output_dir: str = "output"):
    """
    Parses a PDF file using Docling with SmolDocling VLM and exports to structured formats.
    
    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Directory to save output files.
    
    Returns:
        dict: The exported document as a dictionary (structured format).
    """
    # Set up pipeline options with SmolDocling (use SMOLDOCLING_MLX for Apple MPS)
    pipeline_options = VlmPipelineOptions(
        # vlm_options=vlm_model_specs.SMOLDOCLING_MLX,  
        vlm_models = 
        # [
        ## DocTags / SmolDocling models
        vlm_model_specs.SMOLDOCLING_MLX,
        # vlm_model_specs.SMOLDOCLING_TRANSFORMERS,
        ## Markdown models (using MLX framework)
        # vlm_model_specs.QWEN25_VL_3B_MLX,
        # vlm_model_specs.PIXTRAL_12B_MLX,
        # vlm_model_specs.GEMMA3_12B_MLX,
        ## Markdown models (using Transformers framework)
        # vlm_model_specs.GRANITE_VISION_TRANSFORMERS,
        # vlm_model_specs.PHI4_TRANSFORMERS,
        # vlm_model_specs.PIXTRAL_12B_TRANSFORMERS,
        ## More inline models
        # dolphin_oneshot,
        # llava_qwen,
        # ]
        generate_page_images=False,  # if true then pipeline renders each PDF page as an image
        ocr_enabled=True,  # Explicitly enable OCR for scanned documents
        language_hint=["en"]
    )
    
    # Create the converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
                # dip=300 # higher DPI improves accuracy
                # fast_mode=True # it will skip some pre-processing steps
            ),
            InputFormat.IMAGE: PdfFormatOption(  # For image-based inputs
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
            ),
        }
    )
    
    # Convert the PDF
    result = converter.convert(pdf_path)
    doc = result.document
    
    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Get filename stem
    fname = Path(pdf_path).stem
    
    # Export to structured JSON
    json_path = out_path / f"{fname}.json"
    with json_path.open("w") as fp:
        json.dump(doc.export_to_dict(), fp, indent=2)
    print(f"Exported structured JSON to: {json_path}")
    
    # Export to Markdown (human-readable structured format)
    md_path = out_path / f"{fname}.md"
    with md_path.open("w") as fp:
        fp.write(doc.export_to_markdown())
    print(f"Exported Markdown to: {md_path}")
    
    # Export to HTML
    # html_path = out_path / f"{fname}.html"
    # with html_path.open("w") as fp:
    #     fp.write(doc.export_to_html())
    # print(f"Exported HTML to: {html_path}")
    
    # Return the structured dict for further use
    # return doc.export_to_dict()

# Example usage
if __name__ == "__main__":
    pdf_file = "./Contractor_Agreement_Harikrushna_Goti.pdf"  # Replace with your PDF path
    structured_data = parse_pdf_to_structured_format(pdf_file)
    print("Structured data (first 500 chars):", json.dumps(structured_data)[:500])