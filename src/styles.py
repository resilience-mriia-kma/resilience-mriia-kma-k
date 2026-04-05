import streamlit as st


def render_stepper(stepper_labels, current_step, completed_steps):
    """Generate stepper HTML with flexbox for uniform width."""
    stepper_html = "<div style='display: flex; gap: 0.5rem; margin-bottom: 1rem;'>"
    for idx, step_label in enumerate(stepper_labels):
        if idx in completed_steps:
            stepper_html += f"<div class='step-completed'>{step_label}</div>"
        elif idx == current_step:
            stepper_html += f"<div class='step-current'><strong>{step_label}</strong></div>"
        else:
            stepper_html += f"<div class='step-locked'>{step_label}</div>"
    stepper_html += "</div>"
    return stepper_html


def scroll_to_top():
    """Inject JavaScript to scroll to top of main container."""
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    st.markdown(
        '<script>window.parent.document.querySelector("section.main").scrollTo(0,0);</script>',
        unsafe_allow_html=True
    )


def apply_custom_styles():
    """Apply custom CSS styles with purple theme to the Streamlit app."""
    
    st.markdown("""
    <style>
        /* Purple Theme Colors */
        :root {
            --primary-color: #7e57c2;
            --secondary-color: #9575cd;
            --background-color: #f5f5f5;
            --card-background: #ffffff;
            --warning-color: #ffa726;
            --success-color: #2e7d32;
            --text-primary: #212121;
            --text-secondary: #757575;
        }
        
        /* Main container styling */
        .main {
            background-color: var(--background-color);
        }
        
        /* Button styling - Purple theme */
        .stButton > button {
            background-color: var(--primary-color) !important;
            color: white !important;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 2rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: var(--secondary-color) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transform: translateY(-1px);
        }
        
        /* Radio buttons horizontal layout */
        div[role="radiogroup"] {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        /* Progress bar - Purple */
        .stProgress > div > div {
            background-color: var(--primary-color);
        }
        
        /* Input fields - Purple border on focus */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 4px !important;
            border: 1px solid #ddd !important;
            transition: border-color 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #7e57c2 !important;
            box-shadow: 0 0 0 1px #7e57c2 !important;
            outline: none !important;
        }
        
        /* AGGRESSIVE FIX: Hide ALL icons in alerts */
        [data-testid="stNotificationContent"] svg, 
        [data-testid="stIconBlock"],
        .stSuccess svg,
        .stError svg,
        .stWarning svg,
        .stInfo svg {
            display: none !important;
        }
        
        /* AGGRESSIVE FIX: Success - Soft Green */
        div[data-testid="stNotification"][data-test-status="success"],
        .stSuccess {
            background-color: #e8f5e9 !important;
            color: #2e7d32 !important;
            border: none !important;
            border-radius: 8px !important;
        }
        
        /* AGGRESSIVE FIX: Error/Warning - Soft Red */
        div[data-testid="stNotification"][data-test-status="error"],
        div[data-testid="stNotification"][data-test-status="warning"],
        .stError,
        .stWarning {
            background-color: #ffebee !important;
            color: #c62828 !important;
            border: none !important;
            border-radius: 8px !important;
        }
        
        /* Purple Radio Buttons - Simplified (works cross-browser) */
        div[role="radiogroup"] label div[aria-checked="true"] {
            border-color: #7e57c2 !important;
        }
        
        div[role="radiogroup"] label div[aria-checked="true"] > div {
            background-color: #7e57c2 !important;
        }
        
        /* Hide sidebar completely in all browsers */
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Move notifications to top of page */
        div[data-testid="stNotification"] {
            order: -1 !important;
        }
        
        /* Perfect Symmetrical Stepper (Фактор 1-5) */
        .step-completed,
        .step-current,
        .step-locked {
            flex: 1;
            min-width: 0;
            min-height: 80px; /* Фіксована висота для симетрії */
            max-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 10px 5px;
            border-radius: 8px;
            font-size: 0.85rem;
            line-height: 1.1;
            transition: all 0.3s ease;
        }
        
        .step-completed {
            color: #2e7d32 !important;
            font-weight: 600;
            background-color: #e8f5e9 !important;
            border: 2px solid #2e7d32 !important;
        }
        
        .step-current {
            color: #7e57c2 !important;
            font-weight: 700;
            background-color: #f3e5f5 !important;
            border: 2px solid #7e57c2 !important;
            box-shadow: 0 2px 8px rgba(126, 87, 194, 0.2);
        }
        
        .step-locked {
            color: #757575 !important;
            opacity: 0.6;
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
        }
        
        /* Typography */
        h1, h2, h3 {
            color: #212121;
            font-weight: 600;
        }

        /* Remove excessive spacing */
        .block-container {
            padding-top: 1.5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
