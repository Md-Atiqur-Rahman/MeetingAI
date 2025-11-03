# Add to app_gradio.py

with gr.Blocks() as demo:
    # ... existing meeting transcription UI ...
    
    # NEW: AI Conversation Sidebar
    with gr.Column(scale=1):
        gr.Markdown("## 🗣️ AI Conversation Practice")
        
        with gr.Row():
            conv_start_btn = gr.Button("Start Practice", variant="primary")
            conv_stop_btn = gr.Button("Stop", variant="stop")
        
        conv_status = gr.Textbox(label="Status", value="Ready", interactive=False)
        conv_sentiment = gr.Textbox(label="Sentiment", value="😐 Neutral", interactive=False)
        
        conv_chat = gr.Chatbot(label="Conversation", height=400)
        
        conv_stats = gr.Markdown("""
        **Session Stats:**
        - Total messages: 0
        - Grammar errors: 0
        - Avg pronunciation: 0%
        """)
        
        conv_topics = gr.CheckboxGroup(
            label="Next Topics",
            choices=["Continue", "Ask question", "New topic"]
        )
    
    # Event handlers
    def start_conversation():
        # Initialize conversation engine
        pass
    
    def process_conversation_audio(audio):
        # Process user speech
        # Return AI response + feedback
        pass
    
    conv_start_btn.click(start_conversation, outputs=[conv_status])