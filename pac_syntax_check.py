import gradio as gr
import re
import tempfile
import os


def validate_pac_content(content):
    """Validate PAC file content and return results"""
    if not content or not content.strip():
        return "❌ Empty file or no content provided"
    
    errors = []
    warnings = []
    info = []
    
    # 1. Check for required FindProxyForURL function
    find_proxy_pattern = r'function\s+FindProxyForURL\s*\(\s*url\s*,\s*host\s*\)\s*{'
    if not re.search(find_proxy_pattern, content, re.IGNORECASE):
        errors.append("Missing required 'FindProxyForURL(url, host)' function")
    else:
        info.append("✅ Found FindProxyForURL function")
    
    # 2. Check bracket matching
    brackets = 0
    parentheses = 0
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        for char in line:
            if char == '{':
                brackets += 1
            elif char == '}':
                brackets -= 1
                if brackets < 0:
                    errors.append(f"Line {i}: Unmatched closing brace")
            elif char == '(':
                parentheses += 1
            elif char == ')':
                parentheses -= 1
                if parentheses < 0:
                    errors.append(f"Line {i}: Unmatched closing parenthesis")
    
    if brackets > 0:
        errors.append(f"Missing {brackets} closing brace(s)")
    elif brackets < 0:
        errors.append("Extra closing brace(s)")
        
    if parentheses > 0:
        errors.append(f"Missing {parentheses} closing parenthesis")
    elif parentheses < 0:
        errors.append("Extra closing parenthesis")
    
    # 3. Check return statements
    return_pattern = r'return\s+["\'][^"\']*["\']'
    returns = re.findall(return_pattern, content)
    
    if returns:
        info.append(f"Found {len(returns)} return statement(s)")
        
        # Check return values
        valid_prefixes = ['DIRECT', 'PROXY', 'SOCKS', 'HTTP', 'HTTPS']
        for ret in returns:
            value_match = re.search(r'["\']([^"\']*)["\']', ret)
            if value_match:
                value = value_match.group(1).strip()
                if value:
                    is_valid = any(value.upper().startswith(prefix) for prefix in valid_prefixes)
                    if not is_valid:
                        warnings.append(f"Unusual return value: '{value}'")
                    else:
                        info.append(f"Valid return: '{value}'")
    else:
        warnings.append("No return statements found")
    
    # 4. Check for common PAC functions
    pac_functions = [
        'isPlainHostName', 'dnsDomainIs', 'localHostOrDomainIs',
        'isResolvable', 'isInNet', 'dnsResolve', 'myIpAddress',
        'dnsDomainLevels', 'shExpMatch', 'weekdayRange', 'dateRange',
        'timeRange'
    ]
    
    found_functions = []
    for func in pac_functions:
        if func in content:
            found_functions.append(func)
    
    if found_functions:
        info.append(f"PAC functions used: {', '.join(found_functions)}")
    
    # Generate report
    report = []
    
    if errors:
        report.append("🚨 ERRORS:")
        for error in errors:
            report.append(f"  • {error}")
        report.append("")
    
    if warnings:
        report.append("⚠️ WARNINGS:")
        for warning in warnings:
            report.append(f"  • {warning}")
        report.append("")
    
    if info:
        report.append("ℹ️ INFO:")
        for item in info:
            report.append(f"  • {item}")
        report.append("")
    
    # Final verdict
    if not errors:
        report.append("✅ PAC file syntax appears valid!")
        status = "VALID"
    else:
        report.append("❌ PAC file has syntax errors")
        status = "INVALID"
    
    return "\n".join(report), status


def check_pac_file(file):
    """Process uploaded PAC file"""
    if file is None:
        return "Please upload a PAC file", "NO FILE"
    
    try:
        # Read file content
        with open(file.name, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add file info
        file_size = len(content)
        line_count = len(content.split('\n'))
        
        result, status = validate_pac_content(content)
        
        # Prepend file info
        file_info = f"📁 File: {os.path.basename(file.name)}\n"
        file_info += f"📊 Size: {file_size} characters, {line_count} lines\n"
        file_info += "=" * 50 + "\n\n"
        
        return file_info + result, status
        
    except Exception as e:
        return f"❌ Error reading file: {str(e)}", "ERROR"

def check_pac_text(text):
    """Process PAC content from text input"""
    if not text or not text.strip():
        return "Please enter PAC file content", "NO CONTENT"
    
    result, status = validate_pac_content(text)
    
    # Add content info
    content_info = f"📊 Content: {len(text)} characters, {len(text.split())} lines\n"
    content_info += "=" * 50 + "\n\n"
    
    return content_info + result, status

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="PAC File Syntax Checker", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🔍 PAC File Syntax Checker")
        gr.Markdown("Upload a PAC file or paste content to check for syntax errors and validate structure.")
        
        with gr.Tabs():
            # File upload tab
            with gr.TabItem("📁 Upload File"):
                file_input = gr.File(
                    label="Upload PAC File",
                    file_types=[".pac", ".js", ".txt"],
                    type="filepath"
                )
                file_button = gr.Button("Check PAC File", variant="primary")
                file_output = gr.Textbox(
                    label="Validation Results",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )
                file_status = gr.Textbox(label="Status", interactive=False, visible=False)
            
            # Text input tab
            with gr.TabItem("📝 Paste Content"):
                text_input = gr.Textbox(
                    label="PAC File Content",
                    lines=10,
                    placeholder="Paste your PAC file content here...",
                    max_lines=15
                )
                text_button = gr.Button("Check Content", variant="primary")
                text_output = gr.Textbox(
                    label="Validation Results",
                    lines=15,
                    max_lines=20,
                    interactive=False
                )
                text_status = gr.Textbox(label="Status", interactive=False, visible=False)
        
        # Example section
        with gr.Accordion("📖 PAC File Example", open=False):
            gr.Code(
                value='''function FindProxyForURL(url, host) {
    // Direct connection for local hosts
    if (isPlainHostName(host) || 
        dnsDomainIs(host, ".local") ||
        isInNet(host, "192.168.0.0", "255.255.0.0")) {
        return "DIRECT";
    }
    
    // Use proxy for external sites
    return "PROXY proxy.company.com:8080; DIRECT";
}''',
                language="javascript",
                label="Sample PAC File"
            )
        
        # Event handlers
        file_button.click(
            fn=check_pac_file,
            inputs=[file_input],
            outputs=[file_output, file_status]
        )
        
        text_button.click(
            fn=check_pac_text,
            inputs=[text_input],
            outputs=[text_output, text_status]
        )
        
        # Auto-check when file is uploaded
        file_input.change(
            fn=check_pac_file,
            inputs=[file_input],
            outputs=[file_output, file_status]
        )
    
    return interface

if __name__ == "__main__":
    # Create and launch the interface
    app = create_interface()
    app.launch(
        server_name="127.0.0.1",  # Allow external access
        server_port=11000,       # Default Gradio port
        share=False,            # Set to True for public sharing
        debug=True
    )
    
    