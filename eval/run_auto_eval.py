import argparse
import csv
import os
import time
import importlib.util

DEFAULT_MODELS = ["llama3:latest", "mistral:latest", "qwen2.5:7b"]

def load_module_from_path(py_path: str):
    py_path = os.path.abspath(py_path)
    spec = importlib.util.spec_from_file_location("assistant_module", py_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from: {py_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

def now_ms() -> int:
    return int(time.time() * 1000)

def read_questions(csv_path: str):
    out = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            out.append({k: (v or "").strip() for k, v in row.items()})
    return out

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def call_assistant(mod, question: str, model: str, image_path: str = ""):
    # Prefer rag_query_ui(user_input, model_name)
    if hasattr(mod, "rag_query_ui"):
        fn = getattr(mod, "rag_query_ui")
        try:
            ans = fn(question, model)  # type: ignore
            return str(ans), "rag_query_ui"
        except TypeError:
            ans = fn(question)  # type: ignore
            return str(ans), "rag_query_ui_1arg"

    # Fallback to multimodal_query(text_input, image_input, model_name)
    if hasattr(mod, "multimodal_query"):
        fn = getattr(mod, "multimodal_query")
        img = image_path if image_path else None
        try:
            ans = fn(question, img, model)  # type: ignore
            return str(ans), "multimodal_query"
        except TypeError:
            ans = fn(question, img)  # type: ignore
            return str(ans), "multimodal_query_2arg"

    raise RuntimeError("Assistant module must expose rag_query_ui or multimodal_query.")

def summarize(results_csv: str, summary_csv: str):
    # pandas is optional; if missing, skip summary
    try:
        import pandas as pd
    except Exception:
        print("pandas not available; skipping summary file.")
        return

    df = pd.read_csv(results_csv)
    df["is_error"] = df["error"].fillna("").astype(str).str.len() > 0

    grp = df.groupby(["category","model"], dropna=False).agg(
        n=("qid","count"),
        errors=("is_error","sum"),
        avg_latency_ms=("latency_ms","mean"),
        p95_latency_ms=("latency_ms", lambda x: float(x.quantile(0.95))),
    ).reset_index()

    grp["error_rate"] = (grp["errors"] / grp["n"]).round(4)
    grp.to_csv(summary_csv, index=False, encoding="utf-8")
    print("Saved summary:", summary_csv)

def main():
    ap = argparse.ArgumentParser(description="Auto-evaluate your VL-RAG assistant across multiple Ollama models.")
    ap.add_argument("--assistant", required=True, help="Path to your assistant python file (FAISS + model dropdown version).")
    ap.add_argument("--questions", required=True, help="Path to questions.csv")
    ap.add_argument("--outdir", default="eval_out", help="Output directory")
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS, help="Models to test (Ollama names)")
    ap.add_argument("--repeat", type=int, default=1, help="Repeat each (question,model) N times")
    args = ap.parse_args()

    ensure_dir(args.outdir)
    results_csv = os.path.join(args.outdir, "results_raw.csv")
    summary_csv = os.path.join(args.outdir, "results_summary.csv")

    print("Loading assistant module:", args.assistant)
    mod = load_module_from_path(args.assistant)

    questions = read_questions(args.questions)
    if not questions:
        raise RuntimeError("No questions loaded.")

    run_id = f"run_{now_ms()}"
    total = len(questions) * len(args.models) * args.repeat
    done = 0

    with open(results_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id","qid","category","model","repeat_i","start_ms","latency_ms","route_fn","question","image_path","answer","error"])

        for q in questions:
            qid = q.get("id","")
            cat = q.get("category","")
            question = q.get("question","")
            image_path = q.get("image_path","")

            for model in args.models:
                for i in range(args.repeat):
                    done += 1
                    t0 = time.perf_counter()
                    start_ms = now_ms()
                    try:
                        ans, route_fn = call_assistant(mod, question, model, image_path=image_path)
                        err = ""
                    except Exception as e:
                        ans = ""
                        route_fn = ""
                        err = f"{type(e).__name__}: {e}"
                    latency_ms = int((time.perf_counter() - t0) * 1000)

                    w.writerow([run_id, qid, cat, model, i+1, start_ms, latency_ms, route_fn, question, image_path, ans, err])
                    print(f"[{done}/{total}] {qid} | {cat} | {model} | {latency_ms}ms" + ("  (ERROR)" if err else ""))

    print("\nSaved raw results:", results_csv)
    summarize(results_csv, summary_csv)

    print("\nTip for manual scoring (RAG/visual):")
    print(" - Open results_raw.csv and add a column: human_label = {Correct, Partial, Wrong, Hallucination}")
    print(" - Then compute accuracy per model from that label.")

if __name__ == "__main__":
    main()
