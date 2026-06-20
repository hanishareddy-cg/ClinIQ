"""
BERTScore evaluation for ClinIQ retrieval pipeline.

Requires:
  - Backend running at localhost:8000  (uvicorn backend.main:app)
  - Ollama running at localhost:11434

Usage:
  python scripts/05_bertscore_eval.py
"""

import json
import time
from pathlib import Path

import httpx
from bert_score import score as bert_score

REFERENCE_FILE = Path(__file__).parent / "eval" / "reference_qa.json"
API_URL = "http://localhost:8000/api/v1/query"
TIMEOUT = 120.0


def run_query(patient_id: int, question: str) -> str:
    response = httpx.post(
        API_URL,
        json={"patient_id": patient_id, "question": question},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["answer"]


def main():
    qa_pairs = json.loads(REFERENCE_FILE.read_text())

    print(f"Running {len(qa_pairs)} evaluation queries...\n")
    print(f"{'ID':<6} {'Patient':<10} {'Type':<12} {'Status'}")
    print("-" * 50)

    generated = []
    references = []
    failed = []

    for qa in qa_pairs:
        try:
            answer = run_query(qa["patient_id"], qa["question"])
            generated.append(answer)
            references.append(qa["reference"])
            print(f"{qa['id']:<6} {qa['patient_id']:<10} {qa['query_type']:<12} ✓")
            time.sleep(1)  # avoid hammering Ollama
        except Exception as e:
            print(f"{qa['id']:<6} {qa['patient_id']:<10} {qa['query_type']:<12} ✗ {e}")
            failed.append(qa["id"])

    if not generated:
        print("\nNo answers generated. Is the backend running?")
        return

    print(f"\nComputing BERTScore for {len(generated)} answers...")
    print("(downloading model on first run — ~500MB, one time only)\n")

    P, R, F1 = bert_score(
        generated,
        references,
        lang="en",
        model_type="roberta-large",
        verbose=False,
    )

    # ── Per-query results ──────────────────────────────────────────────────
    print(f"\n{'ID':<6} {'Patient':<10} {'Type':<14} {'Precision':<12} {'Recall':<10} {'F1'}")
    print("-" * 65)

    successful = [qa for qa in qa_pairs if qa["id"] not in failed]
    for i, qa in enumerate(successful):
        print(
            f"{qa['id']:<6} {qa['patient_id']:<10} {qa['query_type']:<14} "
            f"{P[i].item():.4f}      {R[i].item():.4f}    {F1[i].item():.4f}"
        )

    # ── Aggregate scores ───────────────────────────────────────────────────
    avg_p  = P.mean().item()
    avg_r  = R.mean().item()
    avg_f1 = F1.mean().item()

    print("\n" + "=" * 65)
    print(f"{'AVERAGE':<6} {'':10} {'':14} {avg_p:<12.4f} {avg_r:<10.4f} {avg_f1:.4f}")
    print("=" * 65)

    # ── Per query-type breakdown ───────────────────────────────────────────
    type_scores: dict[str, list[float]] = {}
    for i, qa in enumerate(successful):
        qt = qa["query_type"]
        type_scores.setdefault(qt, [])
        type_scores[qt].append(F1[i].item())

    print("\nF1 by query type:")
    for qt, scores in sorted(type_scores.items()):
        avg = sum(scores) / len(scores)
        print(f"  {qt:<14} {avg:.4f}  (n={len(scores)})")

    if failed:
        print(f"\nFailed queries: {failed}")

    print(f"\nFinal BERTScore F1: {avg_f1:.4f}")
    if avg_f1 >= 0.80:
        print("✓ Meets 0.80+ threshold")
    else:
        print(f"✗ Below 0.80 threshold (gap: {0.80 - avg_f1:.4f})")


if __name__ == "__main__":
    main()
