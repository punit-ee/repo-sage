"""Streamlit web application for repo-sage."""

import os

import streamlit as st

from repo_sage import RepoAgent, SearchEngine, read_repo_data
from repo_sage.chunking import DocumentChunker, SlidingWindowStrategy

# Page config
st.set_page_config(
    page_title="Repo-Sage: AI Repository Q&A",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize session state
def init_session_state() -> None:
    """Initialize session state variables."""
    if "engine" not in st.session_state:
        st.session_state.engine = None
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "repo_loaded" not in st.session_state:
        st.session_state.repo_loaded = False


@st.cache_resource(show_spinner=False)
def load_repository(
    repo_owner: str, repo_name: str, branch: str = "main"
) -> tuple[SearchEngine, int, int]:
    """Load and index repository (cached)."""
    # Download
    documents = read_repo_data(repo_owner, repo_name, branch)

    # Chunk
    strategy = SlidingWindowStrategy(window_size=1500, step_size=750)
    chunker = DocumentChunker(strategy)
    chunks = chunker.chunk_documents(documents)
    chunk_dicts = [chunk.to_dict() for chunk in chunks]

    # Index
    engine = SearchEngine(text_fields=["content"])
    engine.fit(chunk_dicts)

    return engine, len(documents), len(chunk_dicts)


def main() -> None:
    """Main application."""
    init_session_state()

    # Title
    st.title("💬 Repo-Sage: AI Repository Q&A")
    st.markdown("Chat with any GitHub repository's documentation using AI")

    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")

        # Repository input
        st.subheader("📁 Repository")

        # Popular repos as examples
        example_repos = {
            "Java Design Patterns": ("iluwatar", "java-design-patterns", "master"),
            "DataTalks.Club FAQ": ("DataTalksClub", "faq", "main"),
            "FastAPI": ("tiangolo", "fastapi", "master"),
            "Custom...": ("", "", "main"),
        }

        selected_repo = st.selectbox(
            "Choose a repository",
            list(example_repos.keys()),
            index=0,
        )

        if selected_repo == "Custom...":
            repo_owner = st.text_input("Repository Owner", value="")
            repo_name = st.text_input("Repository Name", value="")
            branch = st.text_input("Branch", value="main")
        else:
            repo_owner, repo_name, branch = example_repos[selected_repo]
            st.info(f"📦 {repo_owner}/{repo_name}")

        # Load button
        load_button = st.button(
            "🚀 Load Repository", type="primary", use_container_width=True
        )

        if load_button and repo_owner and repo_name:
            with st.spinner(f"Loading {repo_owner}/{repo_name}..."):
                try:
                    engine, num_docs, num_chunks = load_repository(
                        repo_owner, repo_name, branch
                    )
                    st.session_state.engine = engine
                    st.session_state.repo_loaded = True

                    # Create agent
                    st.session_state.agent = RepoAgent(
                        engine, model="openai:gpt-4o-mini", enable_logging=False
                    )

                    st.success(f"✅ Loaded {num_docs} files, {num_chunks} chunks")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # Search settings
        st.divider()
        st.subheader("🔍 Search Settings")

        search_type = st.selectbox(
            "Search Type",
            ["hybrid", "vector", "text"],
            help="Hybrid combines semantic and keyword search",
        )

        if search_type == "hybrid":
            vector_weight = st.slider(
                "Vector Weight",
                0.0,
                1.0,
                0.5,
                0.1,
                help="Higher = more semantic, Lower = more keyword-based",
            )
        else:
            vector_weight = 0.5

        # Status
        st.divider()
        if st.session_state.repo_loaded:
            st.success("✅ Repository Loaded")
        else:
            st.warning("⚠️ No repository loaded")

        # API key check
        if os.getenv("OPENAI_API_KEY"):
            st.success("✅ API Key Set")
        else:
            st.error("❌ Set OPENAI_API_KEY")

    # Main content area
    if not st.session_state.repo_loaded:
        st.info("👈 Load a repository from the sidebar to start")

        st.markdown(
            """
        ### How to use:
        1. Choose a repository (or enter custom)
        2. Click "Load Repository"
        3. Ask questions in the chat

        ### Examples:
        - "How do I install this?"
        - "What is the main purpose of this project?"
        - "Explain the Singleton pattern"
        """
        )
        return

    # Chat interface
    st.subheader("💬 Chat")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if question := st.chat_input("Ask a question about the repository..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.chat_message("user"):
            st.markdown(question)

        # Get answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if st.session_state.agent:
                        # Use AI agent
                        answer = st.session_state.agent.ask(question)
                    else:
                        # Fallback to search only
                        results = st.session_state.engine.search(
                            question,
                            search_type=search_type,
                            top_k=3,
                            vector_weight=vector_weight,
                        )
                        answer = "**Top Search Results:**\n\n"
                        for i, result in enumerate(results, 1):
                            content = result.get("content", "")[:300]
                            answer += f"{i}. {content}...\n\n"

                    st.markdown(answer)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": error_msg}
                    )

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()


if __name__ == "__main__":
    main()
