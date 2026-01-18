import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Palm Industry Content Agent",
    page_icon="🌴",
    layout="wide"
)

# Title and description
st.title("🌴 Palm Industry Content Agent")
st.markdown("Generate engaging social media content for the palm industry with AI-powered captions and real stock photos.")

# Sidebar for API configuration
with st.sidebar:
    st.header("⚙️ API Configuration")
    
    # Try to get API keys from secrets, fall back to user input
    try:
        gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
        unsplash_api_key = st.secrets.get("UNSPLASH_API_KEY", "")
    except:
        gemini_api_key = ""
        unsplash_api_key = ""
    
    # If not in secrets, show input fields
    if not gemini_api_key:
        gemini_api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Get your API key from https://aistudio.google.com/app/apikey"
        )
    else:
        st.success("✅ Gemini API Key loaded")
    
    if not unsplash_api_key:
        unsplash_api_key = st.text_input(
            "Unsplash Access Key",
            type="password",
            help="Get your access key from https://unsplash.com/developers"
        )
    else:
        st.success("✅ Unsplash API Key loaded")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool helps you create social media content by:
    - Generating engaging captions with AI
    - Finding relevant stock photos
    - Exporting content for bulk upload
    """)
    
    # API Key Testing Section
    if gemini_api_key:
        st.markdown("---")
        if st.button("🔍 Test Gemini API"):
            with st.spinner("Testing..."):
                try:
                    genai.configure(api_key=gemini_api_key)
                    models = list(genai.list_models())
                    st.success("✅ Gemini API is working!")
                    st.write("Available models:")
                    for m in models:
                        if 'generateContent' in m.supported_generation_methods:
                            st.text(f"✓ {m.name}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    if unsplash_api_key:
        if st.button("🔍 Test Unsplash API"):
            with st.spinner("Testing..."):
                try:
                    test_url = "https://api.unsplash.com/photos/random"
                    headers = {"Authorization": f"Client-ID {unsplash_api_key}"}
                    response = requests.get(test_url, headers=headers)
                    if response.status_code == 200:
                        st.success("✅ Unsplash API is working!")
                    else:
                        st.error(f"❌ Status {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Initialize session state for storing generated content
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = []

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Content Input")
    
    topic = st.text_input(
        "Enter Topic",
        placeholder="e.g., Harvesting Dates, Sustainable Farming, Palm Oil Benefits",
        help="Enter the topic you want to create content about"
    )
    
    tone = st.selectbox(
        "Caption Tone",
        ["Professional", "Casual", "Educational", "Inspiring", "Informative"],
        help="Select the desired tone for your caption"
    )
    
    max_length = st.slider(
        "Caption Length (words)",
        min_value=20,
        max_value=100,
        value=50,
        help="Maximum number of words for the caption"
    )
    
    generate_btn = st.button("🚀 Generate Content", type="primary", use_container_width=True)

with col2:
    st.subheader("📊 Generated Content")
    content_placeholder = st.empty()

# Function to generate caption using Gemini - UPDATED VERSION
def generate_caption(topic, tone, max_length, api_key):
    try:
        genai.configure(api_key=api_key)
        
        # Use the correct current model name
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = f"""Create a {tone.lower()} social media caption about "{topic}" for the palm industry. 
        The caption should be engaging, informative, and suitable for platforms like Instagram or LinkedIn.
        Maximum length: {max_length} words.
        Include relevant hashtags at the end.
        Focus on the palm industry context."""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        
        # If model not found, try alternative models
        if "404" in error_msg or "not found" in error_msg:
            try:
                # Try the latest stable model
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                response = model.generate_content(prompt)
                return response.text
            except:
                try:
                    # Try pro version
                    model = genai.GenerativeModel('models/gemini-1.5-pro')
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e2:
                    return f"❌ Error: Unable to find working Gemini model.\n\nOriginal error: {error_msg}\n\nPlease verify your API key at: https://aistudio.google.com/app/apikey\n\nTip: Click 'Test Gemini API' button in sidebar to see available models."
        
        return f"❌ Error generating caption: {error_msg}\n\nPlease check your API key."

# Function to fetch image from Unsplash
def fetch_unsplash_image(query, api_key):
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {api_key}"}
        params = {
            "query": f"palm {query}",
            "per_page": 1,
            "orientation": "landscape"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['results']:
            photo = data['results'][0]
            return {
                'url': photo['urls']['regular'],
                'thumb_url': photo['urls']['thumb'],
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'download_url': photo['links']['download']
            }
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching image: {str(e)}")
        return None

# Generate content when button is clicked
if generate_btn:
    if not gemini_api_key:
        st.error("⚠️ Please enter your Google Gemini API key in the sidebar.")
    elif not unsplash_api_key:
        st.error("⚠️ Please enter your Unsplash API key in the sidebar.")
    elif not topic:
        st.error("⚠️ Please enter a topic.")
    else:
        with st.spinner("🤖 Generating caption..."):
            caption = generate_caption(topic, tone, max_length, gemini_api_key)
        
        # Check if caption generation was successful
        if "❌" not in caption:
            with st.spinner("🖼️ Fetching image..."):
                image_data = fetch_unsplash_image(topic, unsplash_api_key)
            
            if image_data:
                # Display generated content
                with content_placeholder.container():
                    img_col, text_col = st.columns([1, 1])
                    
                    with img_col:
                        st.image(image_data['url'], use_container_width=True)
                        st.caption(f"📷 Photo by [{image_data['photographer']}]({image_data['photographer_url']}) on Unsplash")
                    
                    with text_col:
                        st.markdown("**Generated Caption:**")
                        st.info(caption)
                
                # Add to session state
                st.session_state.generated_content.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'topic': topic,
                    'tone': tone,
                    'caption': caption,
                    'image_url': image_data['url'],
                    'photographer': image_data['photographer'],
                    'photographer_url': image_data['photographer_url']
                })
                
                st.success("✅ Content generated successfully!")
            else:
                # Show caption even without image
                with content_placeholder.container():
                    st.markdown("**Generated Caption:**")
                    st.info(caption)
                    st.warning("⚠️ No image found for this topic. Try a different search term.")
        else:
            # Show error message
            with content_placeholder.container():
                st.error(caption)

# Display content history
if st.session_state.generated_content:
    st.markdown("---")
    st.subheader("📚 Content History")
    
    # Create DataFrame
    df = pd.DataFrame(st.session_state.generated_content)
    
    # Display table
    st.dataframe(
        df[['timestamp', 'topic', 'tone', 'caption']],
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    col_download, col_clear = st.columns([3, 1])
    
    with col_download:
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"palm_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_clear:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.generated_content = []
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🌴 Palm Industry Content Agent | Powered by Google Gemini & Unsplash"
    "</div>",
    unsafe_allow_html=True
)
