from __future__ import annotations

from typing import Dict, List, Optional


_sentiment_pipeline = None
_zero_shot_pipeline = None


def _lazy_import_transformers():
    try:
        from transformers import pipeline  # type: ignore
        return pipeline
    except Exception:
        return None


def analyze_sentiment_finbert(text: str) -> Optional[Dict[str, float]]:
    """Use FinBERT fine-tuned on Financial Shenanigans book for sentiment analysis.
    
    Uses model:
    - harikrushna2272/finbert-shenanigans
    
    This model is specifically trained to detect financial manipulation patterns
    and questionable accounting practices based on the Financial Shenanigans book.
    """
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        pipeline = _lazy_import_transformers()
        if pipeline is None:
            return None
        try:
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="harikrushna2272/finbert-shenanigans",
                truncation=True
            )
        except Exception:
            # Fallback to standard FinBERT if shenanigans model fails
            try:
                _sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert",
                    truncation=True
                )
            except Exception:
                _sentiment_pipeline = None
        if _sentiment_pipeline is None:
            return None
    try:
        result = _sentiment_pipeline(text[:2048])  # type: ignore[operator]
        if isinstance(result, list) and result:
            item = result[0]
            label = str(item.get("label", "NEUTRAL")).lower()
            score = float(item.get("score", 0.0))
            positive = score if "pos" in label else 0.0
            negative = score if "neg" in label else 0.0
            neutral = score if "neu" in label or label == "neutral" else 0.0
            return {
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
                "label": label,
            }
    except Exception:
        return None
    return None


def detect_financial_shenanigans(text: str) -> Optional[Dict[str, float]]:
    """
    Specialized function to detect potential financial shenanigans patterns
    using the fine-tuned FinBERT model.
    
    Returns:
        Dict with probabilities for different types of financial manipulation patterns,
        or None if the model is not available.
    """
    global _shenanigans_pipeline
    if not hasattr(detect_financial_shenanigans, '_shenanigans_pipeline'):
        _shenanigans_pipeline = None
        pipeline = _lazy_import_transformers()
        if pipeline is not None:
            try:
                _shenanigans_pipeline = pipeline(
                    "text-classification",
                    model="harikrushna2272/finbert-shenanigans",
                    truncation=True
                )
            except Exception:
                _shenanigans_pipeline = None
    
    if _shenanigans_pipeline is None:
        return None
        
    try:
        result = _shenanigans_pipeline(text[:2048])
        if isinstance(result, list) and result:
            patterns = {}
            for pred in result:
                label = str(pred.get("label", "NORMAL")).lower()
                score = float(pred.get("score", 0.0))
                patterns[label] = score
            return patterns
    except Exception:
        return None
    
    return None

def detect_risk_fingpt(text: str) -> Optional[List[str]]:
    """Use GPT4-style model for financial risk analysis if available, else None.

    Tries models:
    - jkpeer/fingpt-sentiment
    - phidata/fingpt-sentiment
    """
    global _zero_shot_pipeline
    if labels is None:
        labels = [
            "market risk",
            "credit risk",
            "liquidity risk",
            "operational risk",
            "compliance risk",
            "legal risk",
            "reputational risk",
            "strategic risk",
            "cybersecurity risk",
        ]
    if _zero_shot_pipeline is None:
        pipeline = _lazy_import_transformers()
        if pipeline is None:
            return None
        try:
            _zero_shot_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        except Exception:
            return None
    try:
        res = _zero_shot_pipeline(text[:2048], labels, multi_label=True)  # type: ignore[operator]
        scores = res.get("scores") if isinstance(res, dict) else None
        candidate_labels = res.get("labels") if isinstance(res, dict) else None
        if not scores or not candidate_labels:
            return None
        out: Dict[str, float] = {}
        for label, score in zip(candidate_labels, scores):
            try:
                out[str(label).replace(" ", "_")] = float(score)
            except Exception:
                continue
        return out
    except Exception:
        return None


