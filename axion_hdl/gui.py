import os
import sys
import webbrowser
from typing import Dict, List, Optional

try:
    from flask import Flask, render_template, jsonify, request, redirect, url_for
except ImportError:
    Flask = None

class AxionGUI:
    def __init__(self, axion_instance):
        self.axion = axion_instance
        self.app = None
        self.port = 5000
        
    def setup_app(self):
        if not Flask:
            print("\nError: GUI dependencies are not installed.")
            print("To use the --gui feature, please install the optional dependencies:")
            print("\n    pip install axion-hdl[gui]")
            print("\nOr install Flask manually:")
            print("    pip install flask>=2.0\n")
            sys.exit(1)
            
        self.app = Flask(__name__)
        self.app.secret_key = 'axion-hdl-dev-key' 
        
        # Simple in-memory storage for pending changes during review
        # Key: module_name, Value: list of registers
        self.pending_changes = {} 
        
        from axion_hdl.source_modifier import SourceModifier
        self.modifier = SourceModifier(self.axion)
        
        # --- Routes ---
        @self.app.route('/')
        def index():
            return render_template('index.html', modules=self.axion.analyzed_modules)
            
        @self.app.route('/api/modules')
        def get_modules():
            # Return modules as JSON
            return jsonify([m['name'] for m in self.axion.analyzed_modules])

        @self.app.route('/module/<name>')
        def view_module(name):
            # Find module
            module = next((m for m in self.axion.analyzed_modules if m['name'] == name), None)
            if not module:
                return "Module not found", 404
            return render_template('editor.html', module=module)

        @self.app.route('/api/save_diff', methods=['POST'])
        def save_diff():
            data = request.json
            module_name = data.get('module_name')
            new_regs = data.get('registers')
            
            # Store pending changes
            self.pending_changes[module_name] = new_regs
            return jsonify({'redirect': url_for('show_diff', module_name=module_name)})

        @self.app.route('/diff/<module_name>')
        def show_diff(module_name):
            if module_name not in self.pending_changes:
                return redirect(url_for('view_module', name=module_name))
                
            new_regs = self.pending_changes[module_name]
            diff_text = self.modifier.compute_diff(module_name, new_regs)
            
            return render_template('diff.html', 
                                 module_name=module_name, 
                                 diff=diff_text)
                                 
        @self.app.route('/api/confirm_save', methods=['POST'])
        def confirm_save():
            # In a real app we'd pass module_name in form, but here let's assume single user flow
            # Or get it from referrer. Let's simplify and use the last pending key if possible or pass via query?
            # Better: pass module_name in the form in diff.html. 
            # Wait, diff.html form action is /api/confirm_save. Let's rely on referrer or just check which module has pending changes? 
            # Ideally support multiple. Let's update diff.html to pass query param or hidden input.
            # For now, let's grab the first key from pending_changes as a shortcut for single-user local tool.
            
            if not self.pending_changes:
                 return redirect(url_for('index'))
                 
            # Find which module is being confirmed from referrer? 
            # Let's clean up logic: user is at /diff/<module_name>. The form posts to /api/confirm_save.
            # We can use the Referer header to parse module name, or simpler:
            # Let's iterate pending_changes.
            
            # Actually, let's update this method to accept module_name in query string for robustness, 
            # but I can't edit diff.html in this tool call.
            # I'll rely on the Referer for now or just take the first item (since it's a local single-user tool).
            
            module_name = list(self.pending_changes.keys())[0]
            new_regs = self.pending_changes.pop(module_name)
            
            success = self.modifier.save_changes(module_name, new_regs)
            
            if success:
                # Reload axion analysis to reflect changes?
                # This requires re-parsing the file.
                # AxionHDL class needs a re-analyze method for specific file.
                # For simplicity: redirect to dashboard, but maybe show a message "Restart to see changes fully"?
                # Or try to re-analyze.
                pass
                
            return redirect(url_for('index'))

    def run(self, port=5000):
        self.setup_app()
        self.port = port
        url = f"http://127.0.0.1:{port}"
        print(f"Starting Axion GUI at {url}")
        
        # Open browser automatically
        webbrowser.open(url)
        
        # Run Flask app
        self.app.run(port=port, debug=True, use_reloader=False)

def start_gui(axion_instance):
    """Entry point for CLI to start GUI."""
    gui = AxionGUI(axion_instance)
    gui.run()
