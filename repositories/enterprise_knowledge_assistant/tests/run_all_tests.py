"""
Enterprise Knowledge Assistant - Unified Test Suite Runner
Runs core unit and integration tests across RAG, LangGraph, Guardrails, and MCP.
"""

import sys
import time
import subprocess

TEST_MODULES = [
    ("Document Loader", "tests.test_document_loader"),
    ("Text Chunker", "tests.test_chunker"),
    ("Embedding Model", "tests.test_embeddings"),
    ("Vector Store (ChromaDB)", "tests.test_vector_store"),
    ("Retriever Component", "tests.test_retriever"),
    ("Presidio Analyzer Config", "tests.test_presidio_config"),
    ("PII Sanitization & Rules", "tests.test_pii_sanitization"),
    ("Input Guardrails", "tests.test_input_guard"),
    ("Output Guardrails", "tests.test_output_guard"),
    ("LangGraph Workflow Compile", "tests.test_workflow"),
    ("Retriever Agent Node", "tests.test_retriever_agent"),
    ("Input Guard Node", "tests.test_input_guard_node"),
    ("Output Guard Node", "tests.test_output_guard_node"),
    ("MCP Graph Action", "tests.test_mcp_graph"),
    ("PII Graph Blocking", "tests.test_full_graph"),
]


def run_suite():
    print("=" * 70)
    print("  ENTERPRISE KNOWLEDGE ASSISTANT — TEST SUITE")
    print("=" * 70)
    print()

    passed = 0
    failed = 0
    start_time = time.time()

    for name, module in TEST_MODULES:
        print(f"[*] Running: {name} ({module})...", end=" ", flush=True)
        try:
            res = subprocess.run(
                [sys.executable, "-m", module],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if res.returncode == 0:
                print("[\033[92mPASS\033[0m]")
                passed += 1
            else:
                print("[\033[91mFAIL\033[0m]")
                failed += 1
                err_text = (res.stderr or res.stdout).strip()
                if err_text:
                    last_lines = "\n".join(err_text.splitlines()[-3:])
                    print(f"    Details: {last_lines}")
        except subprocess.TimeoutExpired:
            print("[\033[93mTIMEOUT\033[0m]")
            failed += 1
        except Exception as err:
            print("[\033[91mERROR\033[0m]")
            print(f"    Exception: {err}")
            failed += 1

    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"  TEST RUN SUMMARY: {passed} Passed, {failed} Failed (Total: {len(TEST_MODULES)}) in {elapsed:.2f}s")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)
