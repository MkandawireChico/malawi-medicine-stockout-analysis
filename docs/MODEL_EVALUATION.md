# Model Evaluation

This project uses a simple baseline classifier to demonstrate stock-out risk classification with transparent, explainable logic. The model is intentionally lightweight and is designed as a baseline for comparison rather than a final operational decision engine.

## Prediction target
The model predicts whether a facility-medicine combination is likely to be in a risk state (low stock or stock-out) in the next reporting window.

## Notes on leakage prevention
- Model inputs are restricted to information available at the reporting date.
- No future deliveries or post-outcome balances are used in features.
- Chronological evaluation is the intended default for future improvements.

## Baseline metrics
The evaluation script produces a small set of metrics including accuracy, precision, recall, F1, and confusion matrix. These metrics are intended for comparison against stronger models in future work.

## Interpretation
Model coefficients and feature importance are not proof of causation. They are operational signals for prioritization and human review, not direct cause statements.
