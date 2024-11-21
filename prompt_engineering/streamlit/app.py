import logging
import os  # for using env variables
import sys  # for appending more paths

current_dir = os.path.dirname(os.path.abspath(__file__))
kit_dir = os.path.abspath(os.path.join(current_dir, '..'))
repo_dir = os.path.abspath(os.path.join(kit_dir, '..'))

sys.path.append(kit_dir)
sys.path.append(repo_dir)

import base64  # for showing the SVG Sambanova icon
from typing import Any

import streamlit as st  # for GUI elements, secrets management
from dotenv import load_dotenv  # for loading env variables

from prompt_engineering.src.llm_management import LLMManager

# Load env variables
load_dotenv(os.path.join(repo_dir, '.env'))

logging.basicConfig(level=logging.INFO)
logging.info('URL: https://localhost:8501')


@st.cache_data
def call_api(llm_manager: LLMManager, prompt: str, llm_expert: str) -> Any:
    """Calls the API endpoint. Uses an input prompt and returns a completion of it.

    Args:
        llm_manager (LLMManager): llm manager object
        prompt (str): prompt text
        llm_expert (str): selected expert model

    Returns:
        Completion of the input prompt
    """
    # Setting llm
    llm = llm_manager.set_llm(model_expert=llm_expert)

    # Get completion from llm
    completion_text = llm.invoke(prompt)
    return completion_text


def render_svg(svg_path: str) -> None:
    """Renders the given svg string.

    Args:
        svg_path (str): SVG file path
    """
    with open(svg_path, 'r') as file:
        svg = file.read()
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    html = r'<img src="data:image/svg+xml;base64,%s" width="60"/>' % b64
    st.write(html, unsafe_allow_html=True)


def generate_crud_prompt(
    framework: str, table_name: str, columns: list[dict]
) -> str:
    """Generates the prompt for CRUD code based on user input.

    Args:
        framework (str): Selected framework
        table_name (str): Table name
        columns (list[dict]): List of column details

    Returns:
        str: Generated prompt
    """
    columns_description = []
    for column in columns:
        column_desc = f"{column['name']} ({column['type']})"
        if column['required']:
            column_desc += " [required]"
        if column['unique']:
            column_desc += " [unique]"
        if column['has_relation']:
            column_desc += f" [relation to {column['relation_entity']}]"
        if column['custom']:
            column_desc += f" [custom request: {column['custom_request']}]"
        columns_description.append(column_desc)
    columns_text = "\n".join(columns_description)

    return f"""
Generate CRUD operations for the {framework} framework.
Table Name: {table_name}
Columns:
{columns_text}
""" 


def generate_css_conversion_prompt(css_framework: str, ui_framework: str, css_code: str, custom_font: str) -> str:
    """Generates the prompt for converting CSS code to another framework.

    Args:
        css_framework (str): Selected CSS framework
        ui_framework (str): Selected UI framework (HTML, React, Next.js, Vue.js)
        css_code (str): Original CSS code to be converted
        custom_font (str): Custom font URL (optional)

    Returns:
        str: Generated prompt
    """
    return f"""
Convert the following CSS code to {css_framework} and {ui_framework}:

CSS Code:
{css_code}

Custom Font (if provided):
{custom_font}
""" 


def main() -> None:
    # Set up title
    st.set_page_config(
        page_title='Full Stack Helper AI',
        layout='centered',
        initial_sidebar_state='auto',
        menu_items={'Get help': 'https://github.com/sambanova/ai-starter-kit/issues/new'},
    )
    col1, mid, col2 = st.columns([1, 1, 20])
    # with col1:
    #     render_svg(os.path.join(kit_dir, 'docs/sambanova-ai.svg'))
    with col2:
        st.title('Full Stack Helper AI')

    # Instantiate LLMManager class
    llm_manager = LLMManager()
    llm_info = llm_manager.llm_info

    # Tabs for CRUD and CSS Converter
    tab1, tab2 = st.tabs(["CRUD Generator", "CSS Converter"])

    with tab1:
        st.header("CRUD Generator")
        # Framework selection
        frameworks = ["Laravel", "Node.js (Express)", "NestJS"]
        framework = st.selectbox("Choose Framework", frameworks)

        # Table name input
        table_name = st.text_input("Table Name", placeholder="Enter table name")

        # Columns setup
        st.write("### Define Columns")
        columns = []
        num_columns = st.number_input("Number of Columns", min_value=1, max_value=20, step=1, value=1)

        for i in range(num_columns):
            # Create a 2-column grid layout for each column definition
            if i % 2 == 0:
                col_left, col_right = st.columns(2)
            current_col = col_left if i % 2 == 0 else col_right

            with current_col:
                st.write(f"#### Column {i + 1}")
                col_name = st.text_input(f"Column {i + 1} Name", key=f"col_name_{i}")
                col_type = st.selectbox(
                    f"Column {i + 1} Type", ["string", "integer", "boolean", "float", "date"], key=f"col_type_{i}"
                )

                # Add checkboxes for Required, Unique, Has Relation, and Custom
                col_required = st.checkbox(f"Required", key=f"col_required_{i}")
                col_unique = st.checkbox(f"Unique", key=f"col_unique_{i}")
                col_has_relation = st.checkbox(f"Has Relation", key=f"col_has_relation_{i}")
                col_custom = st.checkbox(f"Custom", key=f"col_custom_{i}")

                # Relation Entity input if "Has Relation" is checked
                relation_entity = ""
                if col_has_relation:
                    relation_entity = st.text_input(f"Custom Relation Entity (optional)", key=f"relation_entity_{i}")

                # Custom input if "Custom" is checked
                custom_request = ""
                if col_custom:
                    custom_request = st.text_input(f"Custom Request for Column {i + 1} (e.g. 'Slug should be generated based on title')", key=f"custom_request_{i}")

                columns.append(
                    {
                        "name": col_name,
                        "type": col_type,
                        "required": col_required,
                        "unique": col_unique,
                        "has_relation": col_has_relation,
                        "custom": col_custom,
                        "relation_entity": relation_entity,
                        "custom_request": custom_request,
                    }
                )

        # Generate prompt for CRUD
        if st.button("Generate CRUD Code"):
            if not table_name.strip():
                st.error("Table name is required.")
            elif not all(col["name"].strip() for col in columns):
                st.error("All column names are required.")
            else:
                prompt = generate_crud_prompt(framework, table_name, columns)
                llm_expert = llm_info['select_expert']
                response_content = call_api(llm_manager, prompt, llm_expert)
                st.subheader("Generated Code")
                st.code(response_content, language="python")

    with tab2:
        st.header("CSS Framework Converter")
        # CSS framework selection
        css_frameworks = ["Tailwind", "Bootstrap", "Materialize"]
        css_framework = st.selectbox("Choose CSS Framework", css_frameworks)

        # UI Framework selection
        ui_frameworks = ["HTML", "React.js", "Next.js", "Vue.js"]
        ui_framework = st.selectbox("Choose UI Framework", ui_frameworks)

        # Input original CSS code
        css_code = st.text_area("Paste your CSS code here", placeholder="Enter your CSS code...")

        # Input custom font URL
        custom_font = st.text_input("Custom Font URL (optional, e.g. Google Fonts)", placeholder="https://fonts.googleapis.com/css2?family=Roboto&display=swap")

        # Generate prompt for CSS conversion
        if st.button("Convert CSS"):
            if not css_code.strip():
                st.error("CSS code is required.")
            else:
                prompt = generate_css_conversion_prompt(css_framework, ui_framework, css_code, custom_font)
                llm_expert = llm_info['select_expert']
                response_content = call_api(llm_manager, prompt, llm_expert)
                st.subheader(f"Converted CSS ({css_framework}, {ui_framework})")
                st.code(response_content, language="css")


if __name__ == '__main__':
    main()
