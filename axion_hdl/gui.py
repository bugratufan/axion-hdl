import os
import sys
import webbrowser
import json
from typing import Dict, List, Optional

try:
    from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response
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
        
        # Read version from .version file
        self.version = self._read_version()
        
        # Simple in-memory storage for pending changes during review
        # Key: module_name, Value: list of registers
        self.pending_changes = {} 
        
        from axion_hdl.source_modifier import SourceModifier
        from axion_hdl.rule_checker import RuleChecker
        self.modifier = SourceModifier(self.axion)
        self.checker = RuleChecker()
        
        # Inject version into all templates
        @self.app.context_processor
        def inject_version():
            return {'version': self.version}
        
        # --- Routes ---
        @self.app.route('/')
        def index():
            # Re-analyze sources on each dashboard load to pick up new/changed files
            analysis_error = None
            try:
                self.axion.analyzed_modules = []
                self.axion.is_analyzed = False
                self.axion.analyze()
            except Exception as e:
                analysis_error = str(e)
                # Keep any partially analyzed modules
            
            # Run rule checks and compute per-module error/warning counts
            total_errors = 0
            total_warnings = 0
            try:
                self.checker = RuleChecker()  # Reset checker
                
                self.checker.run_all_checks(self.axion.analyzed_modules)
                
                # Inject parsing errors from modules AFTER checks (so they aren't wiped)
                for m in self.axion.analyzed_modules:
                    if 'parsing_errors' in m:
                        for err in m['parsing_errors']:
                            self.checker._add_error("Parsing Error", m['name'], err.get('msg', 'Unknown parsing error'))

                # Also inject global parse errors (e.g. invalid files)
                if hasattr(self.axion, 'parse_errors') and self.axion.parse_errors:
                    import os
                    for err in self.axion.parse_errors:
                        fname = os.path.basename(err.get('file', 'unknown_file'))
                        self.checker._add_error(
                            "Format Error", 
                            fname, 
                            err.get('msg', 'Unknown error')
                        )

                # Build module status map: {module_name: {errors: count, warnings: count}}
                module_status = {}
                for err in self.checker.errors:
                    name = err.get('module', 'unknown')
                    if name not in module_status:
                        module_status[name] = {'errors': 0, 'warnings': 0}
                    module_status[name]['errors'] += 1
                
                for warn in self.checker.warnings:
                    name = warn.get('module', 'unknown')
                    if name not in module_status:
                        module_status[name] = {'errors': 0, 'warnings': 0}
                    module_status[name]['warnings'] += 1
                
                # Attach status to each module
                for m in self.axion.analyzed_modules:
                    status = module_status.get(m['name'], {'errors': 0, 'warnings': 0})
                    m['rule_errors'] = status['errors']
                    m['rule_warnings'] = status['warnings']
                
                total_errors = len(self.checker.errors)
                total_warnings = len(self.checker.warnings)
            except Exception as e:
                if not analysis_error:
                    analysis_error = str(e)
            
            return render_template('index.html', 
                                   modules=self.axion.analyzed_modules,
                                   total_errors=total_errors,
                                   total_warnings=total_warnings,
                                   analysis_error=analysis_error)
            
        @self.app.route('/api/modules')
        def get_modules():
            # Return modules as JSON
            return jsonify([m['name'] for m in self.axion.analyzed_modules])

        @self.app.route('/module/<name>')
        def view_module(name):
            # Handle new module creation
            if name == 'new':
                new_module = {
                    'name': 'new_module',
                    'base_address': 0,
                    'cdc_enabled': False,
                    'cdc_stages': 2,
                    'registers': [],
                    'file': '',
                    'is_new': True
                }
                return render_template('editor.html', module=new_module)
            
            # Find existing module - use file query param if provided for disambiguation
            file_path = request.args.get('file')
            if file_path:
                # Exact match by both name and file
                module = next((m for m in self.axion.analyzed_modules 
                              if m['name'] == name and m['file'] == file_path), None)
            else:
                # Fallback to name-only match
                module = next((m for m in self.axion.analyzed_modules if m['name'] == name), None)
            
            if not module:
                return "Module not found", 404
            module['is_new'] = False
            is_vhdl = module.get('file', '').lower().endswith(('.vhd', '.vhdl'))
            return render_template('editor.html', module=module, is_vhdl=is_vhdl)

        @self.app.route('/rule-check')
        def rule_check_page():
            return render_template('rule_check.html')

        @self.app.route('/api/save_new_module', methods=['POST'])
        def save_new_module():
            """Save a new module to JSON, YAML, or XML file"""
            try:
                data = request.json
                file_path = data.get('file_path')
                module_name = data.get('module_name', 'new_module')
                registers = data.get('registers', [])
                properties = data.get('properties', {})
                format_type = data.get('format', 'json')
                
                if not file_path:
                    return jsonify({'success': False, 'error': 'No file path specified'})
                
                # Parse base address
                base_addr_str = properties.get('base_address', '0000')
                try:
                    if isinstance(base_addr_str, str):
                        base_addr = int(base_addr_str.replace('0x', '').replace('0X', ''), 16)
                    else:
                        base_addr = int(base_addr_str)
                except:
                    base_addr = 0
                
                # Build module data structure for file (matching parser expected format)
                module_data = {
                    'module': module_name,
                    'base_addr': f"0x{base_addr:04X}",
                    'config': {
                        'cdc_en': properties.get('cdc_enabled', False),
                        'cdc_stage': properties.get('cdc_stages', 2)
                    },
                    'registers': []
                }
                
                # Build register list
                for reg in registers:
                    width = int(reg.get('width', 32))
                    reg_data = {
                        'name': reg.get('name', 'unnamed'),
                        'width': width,
                        'access': reg.get('access', 'RW'),
                        'default': reg.get('default_value', '0x0'),
                        'description': reg.get('description', '')
                    }
                    if reg.get('r_strobe'):
                        reg_data['r_strobe'] = True
                    if reg.get('w_strobe'):
                        reg_data['w_strobe'] = True
                    module_data['registers'].append(reg_data)
                
                # Generate content based on format
                if format_type == 'json':
                    import json
                    content = json.dumps(module_data, indent=4)
                elif format_type == 'yaml':
                    try:
                        import yaml
                        content = yaml.dump(module_data, default_flow_style=False, sort_keys=False)
                    except ImportError:
                        return jsonify({'success': False, 'error': 'PyYAML not installed. Run: pip install pyyaml'})
                elif format_type == 'xml':
                    content = self._generate_xml(module_data)
                else:
                    return jsonify({'success': False, 'error': f'Unknown format: {format_type}'})
                
                # Write to file
                with open(file_path, 'w') as f:
                    f.write(content)
                
                return jsonify({'success': True, 'file': file_path})
            except Exception as e:
                import traceback
                return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

        @self.app.route('/generate')
        def generate_page():
            # default to current output dir
            return render_template('generate.html', default_dir=self.axion.output_dir)

        @self.app.route('/api/select_folder')
        def select_folder():
            """Select folder using native dialog (AppleScript on macOS)"""
            import subprocess
            import platform
            
            try:
                if platform.system() == 'Darwin':  # macOS
                    script = '''
                    tell application "System Events"
                        activate
                        set folderPath to POSIX path of (choose folder with prompt "Select Source Directory")
                    end tell
                    '''
                    result = subprocess.run(['osascript', '-e', script], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        folder_path = result.stdout.strip()
                        return jsonify({'path': folder_path})
                    else:
                        return jsonify({'error': 'User cancelled', 'path': ''})
                else:
                    return jsonify({'error': 'Folder selection not supported on this OS', 'path': ''})
            except subprocess.TimeoutExpired:
                return jsonify({'error': 'Selection timed out', 'path': ''})
            except Exception as e:
                return jsonify({'error': str(e), 'path': ''})

        @self.app.route('/api/select_file')
        def select_file():
            """Select file using native dialog (AppleScript on macOS)"""
            import subprocess
            import platform
            
            try:
                if platform.system() == 'Darwin':  # macOS
                    script = '''
                    tell application "System Events"
                        activate
                        set filePath to POSIX path of (choose file with prompt "Select Source File" of type {"vhd", "vhdl", "json", "yaml", "yml", "xml"})
                    end tell
                    '''
                    result = subprocess.run(['osascript', '-e', script], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        file_path = result.stdout.strip()
                        return jsonify({'path': file_path})
                    else:
                        return jsonify({'error': 'User cancelled', 'path': ''})
                else:
                    return jsonify({'error': 'File selection not supported on this OS', 'path': ''})
            except subprocess.TimeoutExpired:
                return jsonify({'error': 'Selection timed out', 'path': ''})
            except Exception as e:
                return jsonify({'error': str(e), 'path': ''})

        @self.app.route('/api/generate', methods=['POST'])
        def run_generate():
            import io
            from contextlib import redirect_stdout
            
            data = request.json
            output_dir = data.get('output_dir')
            formats = data.get('formats', {})
            
            log_capture = io.StringIO()
            success = False
            
            try:
                with redirect_stdout(log_capture):
                    if output_dir:
                        self.axion.set_output_dir(output_dir)
                    
                    # Need to verify analysis first just in case
                    if not self.axion.is_analyzed:
                        print("Re-running analysis...")
                        self.axion.analyze()
                        
                    res = True
                    if formats.get('vhdl'): res &= self.axion.generate_vhdl()
                    if formats.get('xml'): res &= self.axion.generate_xml()
                    if formats.get('yaml'): res &= self.axion.generate_yaml()
                    if formats.get('json'): res &= self.axion.generate_json()
                    if formats.get('header'): res &= self.axion.generate_c_header()
                    if formats.get('doc_md'): res &= self.axion.generate_documentation(format="md")
                    if formats.get('doc_html'): res &= self.axion.generate_documentation(format="html")
                    # Legacy support for old 'doc' format
                    if formats.get('doc') and not formats.get('doc_md') and not formats.get('doc_html'):
                        res &= self.axion.generate_documentation()
                    
                    success = res
                    if success:
                        print("Generation batch completed.")
                    else:
                        print("Some generation tasks failed.")
                        
            except Exception as e:
                import traceback
                traceback.print_exc(file=log_capture)
                success = False

            return jsonify({
                'success': success,
                'logs': log_capture.getvalue().splitlines(),
                'error': log_capture.getvalue() if not success else ''
            })

        @self.app.route('/api/run_check')
        def run_gui_check():
            import io
            from contextlib import redirect_stdout
            
            log_capture = io.StringIO()
            with redirect_stdout(log_capture):
                print("Starting Design Rule Check...")
                
                # Always re-analyze to ensure fresh logs and latest file state
                print("Re-analyzing sources...")
                self.axion.is_analyzed = False
                self.axion.analyzed_modules = []
                self.axion.analyzed_modules = []
                self.axion.analyze()
                
                # First check source file formats for issues
                source_dirs = (
                    self.axion.src_dirs + 
                    self.axion.xml_src_dirs + 
                    self.axion.yaml_src_dirs + 
                    self.axion.json_src_dirs
                )
                print(f"Checking {len(source_dirs)} source directories...")
                
                source_files = (
                    self.axion.src_files +
                    self.axion.xml_src_files +
                    self.axion.yaml_src_files +
                    self.axion.json_src_files
                )
                print(f"Checking {len(source_files)} individual source files...")

                exclude_patterns = list(self.axion._exclude_patterns) if hasattr(self.axion, '_exclude_patterns') else []
                if exclude_patterns:
                    print(f"Excluding patterns: {', '.join(exclude_patterns)}")

                self.checker.check_source_file_formats(source_dirs, exclude_patterns)
                
                # Also check individual source files directly
                for filepath in source_files:
                    print(f"Checking format: {filepath}")
                    self.checker._check_single_file(filepath)
                
                # Then run all module checks
                print(f"Running rule checks on {len(self.axion.analyzed_modules)} analyzed modules...")
                self.checker.run_all_checks(self.axion.analyzed_modules)
                
                print("Rule check completed.")
                
                # Inject parse errors from analysis phase
                if hasattr(self.axion, 'parse_errors') and self.axion.parse_errors:
                    import os
                    print(f"Adding {len(self.axion.parse_errors)} parse errors to results.")
                    for err in self.axion.parse_errors:
                        # Use filename as module name for parse errors
                        fname = os.path.basename(err.get('file', 'unknown_file'))
                        self.checker._add_error(
                            rule_type="Format Error",
                            module_name=fname,
                            message=err.get('msg', 'Unknown error')
                        )

            return jsonify({
                'errors': self.checker.errors,
                'warnings': self.checker.warnings,
                'checked_modules': len(self.axion.analyzed_modules),
                'summary': {
                    'total_errors': len(self.checker.errors),
                    'total_warnings': len(self.checker.warnings),
                    'passed': len(self.checker.errors) == 0
                },
                'logs': log_capture.getvalue().splitlines()
            })

        @self.app.route('/config')
        def config_page():
            return render_template('config.html')

        @self.app.route('/api/config')
        def get_config():
            """Return current configuration as JSON"""
            current_config = {
                'src_dirs': self.axion.src_dirs,
                'src_files': self.axion.src_files,
                'xml_src_dirs': self.axion.xml_src_dirs,
                'xml_src_files': self.axion.xml_src_files,
                'yaml_src_dirs': self.axion.yaml_src_dirs,
                'yaml_src_files': self.axion.yaml_src_files,
                'json_src_dirs': self.axion.json_src_dirs,
                'json_src_files': self.axion.json_src_files,
                'exclude_patterns': list(self.axion._exclude_patterns) if hasattr(self.axion, '_exclude_patterns') else [],
                'output_dir': self.axion.output_dir
            }
            
            # Check for unsaved changes against .axion_conf
            import os
            config_path = os.path.join(os.getcwd(), '.axion_conf')
            unsaved = False
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        saved_config = json.load(f)
                    
                    # Helper to normalize for comparison (sort lists)
                    def normalize(c):
                        n = {}
                        keys = ['src_dirs', 'src_files', 'xml_src_dirs', 'xml_src_files', 
                                'yaml_src_dirs', 'yaml_src_files', 'json_src_dirs', 'json_src_files',
                                'exclude_patterns']
                        for k in keys:
                            # Use empty list if key missing
                            n[k] = sorted(c.get(k, []))
                        n['output_dir'] = c.get('output_dir', '')
                        return n
                    
                    if normalize(current_config) != normalize(saved_config):
                        unsaved = True
                except Exception:
                    # If error reading saved config, consider it unsaved/differs
                    unsaved = True
            
            current_config['unsaved_changes'] = unsaved
            return jsonify(current_config)

        @self.app.route('/api/config/export')
        def export_config():
            """Export config as file download"""
            config = {
                'src_dirs': self.axion.src_dirs,
                'src_files': self.axion.src_files,
                'xml_src_dirs': self.axion.xml_src_dirs,
                'xml_src_files': self.axion.xml_src_files,
                'yaml_src_dirs': self.axion.yaml_src_dirs,
                'yaml_src_files': self.axion.yaml_src_files,
                'json_src_dirs': self.axion.json_src_dirs,
                'json_src_files': self.axion.json_src_files,
                'exclude_patterns': list(self.axion._exclude_patterns) if hasattr(self.axion, '_exclude_patterns') else [],
                'output_dir': self.axion.output_dir
            }
            response = make_response(json.dumps(config, indent=4))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = 'attachment; filename=axion_config.json'
            return response

        @self.app.route('/api/config/refresh', methods=['POST'])
        def refresh_config_api():
            """Reload modules and return logs"""
            import io
            from contextlib import redirect_stdout
            log_capture = io.StringIO()
            success = True
            
            try:
                with redirect_stdout(log_capture):
                     print("Refreshing configuration...")
                     print("Re-scanning sources and parsing modules...")
                     
                     # Force re-analysis similar to run_check
                     self.axion.is_analyzed = False
                     self.axion.analyzed_modules = []
                     self.axion.analyze()
                     
                     print(f"Analysis complete. Found {len(self.axion.analyzed_modules)} modules.")
                     
            except Exception as e:
                import traceback
                traceback.print_exc(file=log_capture)
                success = False

            return jsonify({
                'success': success,
                'logs': log_capture.getvalue().splitlines()
            })

        @self.app.route('/api/config/save', methods=['POST'])
        def save_config_local():
            """Save config to .axion_conf in root"""
            try:
                config = {
                    'src_dirs': self.axion.src_dirs,
                    'src_files': self.axion.src_files,
                    'xml_src_dirs': self.axion.xml_src_dirs,
                    'xml_src_files': self.axion.xml_src_files,
                    'yaml_src_dirs': self.axion.yaml_src_dirs,
                    'yaml_src_files': self.axion.yaml_src_files,
                    'json_src_dirs': self.axion.json_src_dirs,
                    'json_src_files': self.axion.json_src_files,
                    'exclude_patterns': list(self.axion._exclude_patterns) if hasattr(self.axion, '_exclude_patterns') else [],
                    'output_dir': self.axion.output_dir
                }
                config_path = os.path.join(os.getcwd(), '.axion_conf')
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                return jsonify({'success': True, 'path': config_path})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/config/add_source', methods=['POST'])
        def add_source():
            """Add a source path"""
            data = request.json
            path = data.get('path', '').strip()
            path_type = data.get('type', 'dir')  # dir or file
            
            if not path:
                return jsonify({'success': False, 'error': 'No path provided'})
            
            import os
            if not os.path.exists(path):
                return jsonify({'success': False, 'error': f'Path does not exist: {path}'})
            
            try:
                self.axion.add_source(path)
                # Reset analysis flag so dashboard will re-analyze
                self.axion.is_analyzed = False
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/config/remove_source', methods=['POST'])
        def remove_source():
            """Remove a source path"""
            data = request.json
            path = data.get('path', '').strip()
            path_type = data.get('type', 'dir')
            file_type = data.get('file_type', 'vhdl')
            
            if not path:
                return jsonify({'success': False, 'error': 'No path provided'})
            
            try:
                # Remove from appropriate list based on type
                if path_type == 'dir':
                    if file_type == 'vhdl' and path in self.axion.src_dirs:
                        self.axion.src_dirs.remove(path)
                    elif file_type == 'xml' and path in self.axion.xml_src_dirs:
                        self.axion.xml_src_dirs.remove(path)
                    elif file_type == 'yaml' and path in self.axion.yaml_src_dirs:
                        self.axion.yaml_src_dirs.remove(path)
                    elif file_type == 'json' and path in self.axion.json_src_dirs:
                        self.axion.json_src_dirs.remove(path)
                else:
                    if file_type == 'vhdl' and path in self.axion.src_files:
                        self.axion.src_files.remove(path)
                    elif file_type == 'xml' and path in self.axion.xml_src_files:
                        self.axion.xml_src_files.remove(path)
                    elif file_type == 'yaml' and path in self.axion.yaml_src_files:
                        self.axion.yaml_src_files.remove(path)
                    elif file_type == 'json' and path in self.axion.json_src_files:
                        self.axion.json_src_files.remove(path)
                
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/config/add_exclude', methods=['POST'])
        def add_exclude():
            """Add an exclude pattern"""
            data = request.json
            pattern = data.get('pattern', '').strip()
            
            if not pattern:
                return jsonify({'success': False, 'error': 'No pattern provided'})
            
            try:
                self.axion.exclude(pattern)
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/config/remove_exclude', methods=['POST'])
        def remove_exclude():
            """Remove an exclude pattern"""
            data = request.json
            pattern = data.get('pattern', '').strip()
            
            if not pattern:
                return jsonify({'success': False, 'error': 'No pattern provided'})
            
            try:
                if hasattr(self.axion, '_exclude_patterns'):
                    self.axion._exclude_patterns.discard(pattern)
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})

        @self.app.route('/api/config/files')
        def get_detected_files():
            """Get list of all detected source files"""
            import os
            import fnmatch
            
            files_list = []
            exclude_patterns = list(self.axion._exclude_patterns) if hasattr(self.axion, '_exclude_patterns') else []
            
            def is_excluded(filepath):
                filename = os.path.basename(filepath)
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(filename, pattern): return True
                    if pattern in filepath: return True
                return False

            # Add manually added files first
            manual_files = (
                self.axion.src_files + 
                self.axion.xml_src_files + 
                self.axion.yaml_src_files + 
                self.axion.json_src_files
            )
            for f in manual_files:
                if not is_excluded(f) and os.path.exists(f):
                    files_list.append({'path': f, 'type': 'Manual', 'category': 'File'})

            # Scan directories
            dirs = (
                self.axion.src_dirs + 
                self.axion.xml_src_dirs + 
                self.axion.yaml_src_dirs + 
                self.axion.json_src_dirs
            )
            
            unique_paths = {f['path'] for f in files_list}
            
            for d in dirs:
                if not os.path.exists(d): continue
                for root, dirnames, filenames in os.walk(d):
                    # Skip excluded directories
                    dirnames[:] = [d for d in dirnames if not any(fnmatch.fnmatch(d, p) for p in exclude_patterns)]
                    
                    for filename in filenames:
                        filepath = os.path.join(root, filename)
                        
                        if is_excluded(filepath): continue
                        
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in ['.vhd', '.vhdl', '.json', '.yaml', '.yml', '.xml']:
                             if filepath not in unique_paths:
                                 files_list.append({'path': filepath, 'type': 'Scanned', 'category': ext[1:].upper()})
                                 unique_paths.add(filepath)
            
            return jsonify(sorted(files_list, key=lambda x: x['path']))

        @self.app.route('/api/save_diff', methods=['POST'])
        def save_diff():
            data = request.json
            module_name = data.get('module_name')
            file_path = data.get('file_path', '')  # Add file path for disambiguation
            new_regs = data.get('registers')
            props = data.get('properties', {})
            
            # Store pending changes using file_path as unique key (or module_name for new modules)
            change_key = file_path if file_path else module_name
            self.pending_changes[change_key] = {
                'module_name': module_name,
                'file_path': file_path,
                'registers': new_regs,
                'properties': props
            }
            # URL encode the file path for safe routing
            from urllib.parse import quote
            return jsonify({'redirect': f'/diff?key={quote(change_key, safe="")}'})

        @self.app.route('/diff')
        def show_diff():
            from urllib.parse import unquote
            change_key = unquote(request.args.get('key', ''))
            
            if change_key not in self.pending_changes:
                return redirect(url_for('index'))
                
            pending = self.pending_changes[change_key]
            module_name = pending['module_name']
            file_path = pending.get('file_path', '')
            new_regs = pending['registers']
            props = pending.get('properties', {})
            
            # Pass file_path to compute_diff for correct file identification
            diff_text = self.modifier.compute_diff(module_name, new_regs, props, file_path=file_path)
            
            return render_template('diff.html', 
                                 module_name=module_name,
                                 file_path=file_path,
                                 change_key=change_key,
                                 diff=diff_text)
                                 
        @self.app.route('/api/confirm_save', methods=['POST'])
        def confirm_save():
            # Get change_key from form data
            change_key = request.form.get('change_key', '')
            
            if not change_key and self.pending_changes:
                # Fallback: use first pending key if change_key not provided
                change_key = list(self.pending_changes.keys())[0]
            
            if not change_key or change_key not in self.pending_changes:
                return redirect(url_for('index'))
            
            pending = self.pending_changes.pop(change_key)
            module_name = pending.get('module_name', change_key)
            file_path = pending.get('file_path', '')
            new_regs = pending['registers']
            props = pending.get('properties', {})
            
            # Use file_path aware save
            success = self.modifier.save_changes(module_name, new_regs, props, file_path=file_path)
            
            if success:
                # Trigger re-analysis to reflect changes
                try:
                    self.axion.analyzed_modules = []
                    self.axion.is_analyzed = False
                    self.axion.analyze()
                except:
                    pass  # Ignore analysis errors
                
            return redirect(url_for('index'))

    def _generate_vhdl_template(self, module_name, registers, properties):
        """Generate VHDL source code for a new module"""
        base_addr = properties.get('base_address', '0000')
        cdc_enabled = properties.get('cdc_enabled', False)
        cdc_stages = properties.get('cdc_stages', 2)
        
        lines = []
        lines.append("library IEEE;")
        lines.append("use IEEE.STD_LOGIC_1164.ALL;")
        lines.append("use IEEE.NUMERIC_STD.ALL;")
        lines.append("")
        lines.append(f"entity {module_name} is")
        lines.append("    port (")
        lines.append("        clk     : in  std_logic;")
        lines.append("        rst_n   : in  std_logic")
        lines.append("    );")
        lines.append(f"end entity {module_name};")
        lines.append("")
        lines.append(f"architecture rtl of {module_name} is")
        lines.append("")
        lines.append(f"    -- AXION_BASE_ADDRESS: 0x{base_addr}")
        if cdc_enabled:
            lines.append(f"    -- AXION_CDC: {cdc_stages}")
        lines.append("")
        lines.append("    -- AXION_REG_BEGIN")
        
        for reg in registers:
            name = reg.get('name', 'unnamed')
            width = int(reg.get('width', 32))
            access = reg.get('access', 'RW')
            default = reg.get('default_value', '0x0')
            desc = reg.get('description', '')
            r_strobe = reg.get('r_strobe', False)
            w_strobe = reg.get('w_strobe', False)
            
            # Determine signal type
            if width == 1:
                sig_type = "std_logic"
                default_val = "'0'" if default in ['0x0', '0', ''] else "'1'"
            else:
                sig_type = f"std_logic_vector({width-1} downto 0)"
                # Convert hex default to VHDL format
                try:
                    hex_val = default.replace('0x', '').replace('0X', '')
                    int_val = int(hex_val, 16) if hex_val else 0
                    default_val = f'x"{int_val:0{(width+3)//4}X}"'
                except:
                    default_val = f'(others => \'0\')'
            
            # Build comment with access mode and description
            comment_parts = [f"-- {access}"]
            if desc:
                comment_parts.append(desc)
            if r_strobe:
                comment_parts.append("R_STROBE")
            if w_strobe:
                comment_parts.append("W_STROBE")
            comment = " ".join(comment_parts)
            
            lines.append(f"    signal {name} : {sig_type} := {default_val}; {comment}")
        
        lines.append("    -- AXION_REG_END")
        lines.append("")
        lines.append("begin")
        lines.append("")
        lines.append("    -- User logic here")
        lines.append("")
        lines.append(f"end architecture rtl;")
        lines.append("")
        
        return "\n".join(lines)

    def _generate_xml(self, module_data):
        """Generate XML content for a module (matching parser expected format)"""
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append(f'<register_map module="{module_data["module"]}" base_addr="{module_data["base_addr"]}">')
        
        # Config section
        config = module_data.get('config', {})
        cdc_en = str(config.get('cdc_en', False)).lower()
        cdc_stage = config.get('cdc_stage', 2)
        lines.append(f'  <config cdc_en="{cdc_en}" cdc_stage="{cdc_stage}"/>')
        
        # Registers
        for reg in module_data['registers']:
            attrs = [f'name="{reg["name"]}"']
            attrs.append(f'access="{reg["access"]}"')
            attrs.append(f'width="{reg["width"]}"')
            if reg.get('default'):
                attrs.append(f'default="{reg["default"]}"')
            if reg.get('description'):
                attrs.append(f'description="{reg["description"]}"')
            if reg.get('r_strobe'):
                attrs.append('r_strobe="true"')
            if reg.get('w_strobe'):
                attrs.append('w_strobe="true"')
            
            lines.append(f'  <register {" ".join(attrs)}/>')
        
        lines.append('</register_map>')
        return '\n'.join(lines)

    def run(self, port=5050):
        self.setup_app()
        self.port = port
        url = f"http://127.0.0.1:{port}"
        print(f"Starting Axion GUI at {url}")
        
        # Open browser automatically
        webbrowser.open(url)
        
        # Run Flask app
        self.app.run(port=port, debug=True, use_reloader=False)

    def _read_version(self):
        """Read version from .version file."""
        import os
        
        # Try multiple possible locations for .version file
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '.version'),  # Package install
            os.path.join(os.getcwd(), '.version'),  # Current directory
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return f.read().strip()
                except:
                    pass
        
        # Fallback to package version if .version not found
        try:
            from axion_hdl import __version__
            return __version__
        except:
            return "unknown"

def start_gui(axion_instance, port=5000):
    gui = AxionGUI(axion_instance)
    gui.port = port
    gui.run()
