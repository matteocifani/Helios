
import streamlit as st
from contextlib import contextmanager

def get_loader_css():
    """Defines the CSS for the Helios premium loader."""
    return """
    <style>
    /* Helios Premium Loader Container */
    .helios-loader-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        margin: 1rem 0;
        animation: fadeIn 0.3s ease-in-out;
    }

    /* Primary Ring */
    .helios-loader-ring {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 4px solid transparent;
        border-top-color: #00A0B0; /* vs-teal */
        border-bottom-color: #00C9D4; /* vs-cyan */
        animation: spin 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        position: relative;
        filter: drop-shadow(0 0 10px rgba(0, 160, 176, 0.3));
    }

    /* Inner Ring (Sun Core) */
    .helios-loader-ring::before {
        content: "";
        position: absolute;
        top: 6px;
        left: 6px;
        right: 6px;
        bottom: 6px;
        border-radius: 50%;
        border: 3px solid transparent;
        border-left-color: #1B3A5F; /* vs-navy */
        animation: spin-reverse 2s linear infinite;
    }

    /* Center Dot (Helios Core) */
    .helios-loader-ring::after {
        content: "";
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        bottom: 20px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00A0B0 0%, #00C9D4 100%);
        box-shadow: 0 0 15px rgba(0, 160, 176, 0.5);
        animation: pulse-core 1.5s ease-in-out infinite alternate;
    }

    /* Loading Text */
    .helios-loader-text {
        margin-top: 1.5rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #1B3A5F;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        animation: pulse-text 2s ease-in-out infinite;
    }

    /* Animations */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    @keyframes spin-reverse {
        0% { transform: rotate(360deg); }
        100% { transform: rotate(0deg); }
    }

    @keyframes pulse-core {
        0% { transform: scale(0.8); opacity: 0.8; }
        100% { transform: scale(1.1); opacity: 1; }
    }

    @keyframes pulse-text {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Hide default Streamlit spinner if possible/needed, 
       but we are replacing it, so this might not be strictly necessary 
       unless we want to override the top-right one. */
    </style>
    """

def get_loader_html(text="Caricamento in corso..."):
    """Generates the HTML for the loader."""
    return f"""
    <div class="helios-loader-container">
        <div class="helios-loader-ring"></div>
        <div class="helios-loader-text">{text}</div>
    </div>
    """

@contextmanager
def helio_spinner(text="Caricamento..."):
    """
    Context manager that renders a custom Helios-themed spinner.
    Replaces st.spinner with a more premium UI.
    """
    # Create a placeholder
    placeholder = st.empty()
    
    # Render styles (once per run effectively, but safe to include)
    st.markdown(get_loader_css(), unsafe_allow_html=True)
    
    try:
        # Show loader
        placeholder.markdown(get_loader_html(text), unsafe_allow_html=True)
        yield
    finally:
        # Clear loader
        placeholder.empty()
