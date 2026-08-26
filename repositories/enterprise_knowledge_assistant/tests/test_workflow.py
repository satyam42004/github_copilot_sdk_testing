from graph.workflow import build_graph


def main():
    graph = build_graph()

    print("LangGraph workflow compiled successfully.")

    print("\nGraph nodes:")
    for node_name in graph.nodes:
        print(f"- {node_name}")


if __name__ == "__main__":
    main()