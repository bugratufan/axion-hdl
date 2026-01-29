import os
import sys
import webbrowser
import json
import threading
import time
from typing import Dict, List, Optional

try:
    from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response
except ImportError:
    Flask = None

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class AnalysisCache:
    """Cache for analysis results to avoid re-parsing unchanged files"""
    def __init__(self):
        self.last_analysis_time = 0
        self.source_file_mtimes = {}  # {filepath: mtime}
        self.is_analyzing = False
        self.analysis_lock = threading.Lock()

    def needs_refresh(self, axion_instance) -> bool:
        """Check if any source files have changed"""
        # If never analyzed, need refresh
        if not self.source_file_mtimes:
            return True

        all_files = self._get_all_source_files(axion_instance)

        # If file list changed, need refresh
        if set(all_files) != set(self.source_file_mtimes.keys()):
            return True

        # Check if any file modified (with tolerance for file system timestamp precision)
        for filepath in all_files:
            if not os.path.exists(filepath):
                return True
            try:
                current_mtime = os.path.getmtime(filepath)
                cached_mtime = self.source_file_mtimes.get(filepath, 0)
                # Use 1 second tolerance to avoid float comparison issues
                if abs(current_mtime - cached_mtime) > 1:
                    return True
            except OSError:
                return True

        return False

    def update_mtimes(self, axion_instance):
        """Update cached file modification times"""
        all_files = self._get_all_source_files(axion_instance)
        self.source_file_mtimes = {}
        for filepath in all_files:
            if os.path.exists(filepath):
                self.source_file_mtimes[filepath] = os.path.getmtime(filepath)
        self.last_analysis_time = time.time()

    def _get_all_source_files(self, axion_instance) -> List[str]:
        """Get all source files from axion instance"""
        files = []

        # Direct files
        files.extend(axion_instance.src_files)
        files.extend(axion_instance.xml_src_files)
        files.extend(axion_instance.yaml_src_files)
        files.extend(axion_instance.json_src_files)

        # Files from directories
        all_dirs = (
            axion_instance.src_dirs +
            axion_instance.xml_src_dirs +
            axion_instance.yaml_src_dirs +
            axion_instance.json_src_dirs
        )

        for directory in all_dirs:
            if os.path.exists(directory):
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in ['.vhd', '.vhdl', '.json', '.yaml', '.yml', '.xml']:
                            files.append(os.path.join(root, filename))

        return files


class SourceFileEventHandler(FileSystemEventHandler):
    """Watchdog handler for source file changes"""
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.debounce_timer = None
        self.debounce_delay = 2.0  # Wait 2 seconds after last change
        self.last_event_path = None
        self.last_event_time = 0
        self.ignore_patterns = ['.swp', '.tmp', '~', '.bak', '.git', '__pycache__']

    def _should_process_event(self, event):
        """Check if event should be processed"""
        if event.is_directory:
            return False

        # Ignore temp/swap files
        filename = os.path.basename(event.src_path)
        if any(pattern in filename for pattern in self.ignore_patterns):
            return False

        # Check if it's a relevant file
        ext = os.path.splitext(event.src_path)[1].lower()
        if ext not in ['.vhd', '.vhdl', '.json', '.yaml', '.yml', '.xml']:
            return False

        # Ignore duplicate events for same file (within 0.5 seconds)
        current_time = time.time()
        if event.src_path == self.last_event_path and (current_time - self.last_event_time) < 0.5:
            return False

        return True

    def _schedule_analysis(self, event):
        """Schedule analysis with debouncing"""
        self.last_event_path = event.src_path
        self.last_event_time = time.time()

        # Debounce: cancel previous timer and start new one
        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = threading.Timer(self.debounce_delay, self._trigger_analysis)
        self.debounce_timer.start()

    def on_modified(self, event):
        """Handle file modifications"""
        if self._should_process_event(event):
            self._schedule_analysis(event)

    def on_created(self, event):
        """Handle new file creation"""
        if self._should_process_event(event):
            self._schedule_analysis(event)

    def _trigger_analysis(self):
        """Trigger analysis in background"""
        threading.Thread(target=self.gui._background_analyze, daemon=True).start()


class AxionGUI:
    def __init__(self, axion_instance, debug_mode=False):
        self.axion = axion_instance
        self.app = None
        self.port = 5000
        self.debug_mode = debug_mode
        self.analysis_cache = AnalysisCache()
        self.file_observer = None
        self.analysis_error = None
        
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

        # Configure logging based on debug mode
        import logging
        log = logging.getLogger('werkzeug')
        if self.debug_mode:
            log.setLevel(logging.INFO)
        else:
            log.setLevel(logging.ERROR)
            # Also suppress Flask's default banner in non-debug mode
            # Check if running in a way where cli is available (Flask 2.x+)
            if hasattr(self.app, 'cli'):
                self.app.cli.show_server_banner = lambda *args: None

        # Read version from .version file
        self.version = self._read_version()

        # Simple in-memory storage for pending changes during review
        # Key: module_name, Value: list of registers
        self.pending_changes = {}

        from axion_hdl.source_modifier import SourceModifier
        from axion_hdl.rule_checker import RuleChecker
        self.modifier = SourceModifier(self.axion)
        self.checker = RuleChecker()

        # Start file watcher if available
        self._start_file_watcher()

        # Do initial analysis synchronously on first request (not here)
        self.initial_analysis_done = False
        
        # Inject version into all templates
        @self.app.context_processor
        def inject_version():
            return {'version': self.version}
        
        # --- Routes ---
        @self.app.route('/')
        def index():
            import os as os_module
            # Do initial analysis only on first request
            if not self.initial_analysis_done:
                try:
                    self.axion.analyzed_modules = []
                    self.axion.is_analyzed = False
                    self.axion.analyze()

                    # Run initial rule checks
                    from axion_hdl.rule_checker import RuleChecker
                    self.checker = RuleChecker()
                    self.checker.run_all_checks(self.axion.analyzed_modules)

                    # Inject parsing errors
                    for m in self.axion.analyzed_modules:
                        if 'parsing_errors' in m:
                            for err in m['parsing_errors']:
                                self.checker._add_error("Parsing Error", m['name'], err.get('msg', 'Unknown parsing error'))

                    if hasattr(self.axion, 'parse_errors') and self.axion.parse_errors:
                        for err in self.axion.parse_errors:
                            fname = os_module.path.basename(err.get('file', 'unknown_file'))
                            self.checker._add_error("Format Error", fname, err.get('msg', 'Unknown error'))

                    # Build module status map and attach to modules
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

                    self.analysis_cache.update_mtimes(self.axion)
                    self.initial_analysis_done = True
                    self.analysis_error = None
                except Exception as e:
                    self.analysis_error = str(e)

            # Use cached analysis results
            analysis_error = self.analysis_error

            # Ensure all modules have rule_errors and rule_warnings attributes
            for m in self.axion.analyzed_modules:
                if 'rule_errors' not in m:
                    m['rule_errors'] = 0
                if 'rule_warnings' not in m:
                    m['rule_warnings'] = 0

            # Calculate totals from modules
            total_errors = sum(m.get('rule_errors', 0) for m in self.axion.analyzed_modules)
            total_warnings = sum(m.get('rule_warnings', 0) for m in self.axion.analyzed_modules)
            
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
                return render_template('editor.html', module=new_module, server_mode=self.axion.output_dir is None)
            
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
            return render_template('editor.html', module=module, is_vhdl=is_vhdl, server_mode=self.axion.output_dir is None)

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
                        'description': reg.get('description', ''),
                        # Always include address - persist auto-assigned addresses
                        'addr': reg.get('address', '0x0')
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
                
                # Add to sources and re-analyze to show up in list immediately
                self.axion.add_source(file_path)
                self.axion.is_analyzed = False
                self.axion.analyze()
                
                return jsonify({'success': True, 'file': file_path})
            except Exception as e:
                import traceback
                return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

        @self.app.route('/generate')
        def generate_page():
            # default to current output dir, pass no_output_dir flag for UI
            no_output_dir = self.axion.output_dir is None
            return render_template('generate.html', 
                                   default_dir=self.axion.output_dir or '',
                                   no_output_dir=no_output_dir)

        @self.app.route('/api/select_folder')
        def select_folder():
            """Select folder using native dialog (Cross-platform)"""
            import platform
            
            system = platform.system()
            try:
                if system == 'Darwin':
                    return self._select_folder_macos()
                elif system == 'Windows':
                    return self._select_folder_windows()
                elif system == 'Linux':
                    return self._select_folder_linux()
                else:
                    return jsonify({'error': f'Folder selection not supported on {system}', 'path': ''})
            except Exception as e:
                return jsonify({'error': str(e), 'path': ''})

        @self.app.route('/api/select_file')
        def select_file():
            """Select file using native dialog (Cross-platform)"""
            import platform
            
            system = platform.system()
            try:
                if system == 'Darwin':
                    return self._select_file_macos()
                elif system == 'Windows':
                    return self._select_file_windows()
                elif system == 'Linux':
                    return self._select_file_linux()
                else:
                    return jsonify({'error': f'File selection not supported on {system}', 'path': ''})
            except Exception as e:
                return jsonify({'error': str(e), 'path': ''})



        @self.app.route('/api/generate', methods=['POST'])
        def run_generate():
            import io
            import tempfile
            from contextlib import redirect_stdout
            
            data = request.json
            output_dir = data.get('output_dir') or None  # Treat empty string as None
            formats = data.get('formats', {})
            modules_filter = data.get('modules')  # Optional list of module names to generate
            
            log_capture = io.StringIO()
            success = False
            temp_dir_path = None  # For temp+ZIP mode
            used_output_dir = None
            
            try:
                with redirect_stdout(log_capture):
                    # Determine effective output directory
                    if output_dir:
                        self.axion.set_output_dir(output_dir)
                        used_output_dir = output_dir
                    elif self.axion.output_dir:
                        used_output_dir = self.axion.output_dir
                    else:
                        # Temp+ZIP mode: create temporary directory
                        temp_dir = tempfile.mkdtemp(prefix='axion_gen_')
                        self.axion.set_output_dir(temp_dir)
                        temp_dir_path = temp_dir
                        used_output_dir = temp_dir
                        print(f"Using temporary directory: {temp_dir}")
                    
                    # Need to verify analysis first just in case
                    if not self.axion.is_analyzed:
                        print("Re-running analysis...")
                        self.axion.analyze()
                    
                    # Filter modules if specified
                    original_modules = None
                    if modules_filter:
                        original_modules = self.axion.analyzed_modules
                        self.axion.analyzed_modules = [
                            m for m in self.axion.analyzed_modules 
                            if m.get('name') in modules_filter
                        ]
                        print(f"Generating for {len(self.axion.analyzed_modules)} selected module(s): {', '.join(modules_filter)}")
                    
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
                    
                    # Restore original modules list if filtered
                    if original_modules is not None:
                        self.axion.analyzed_modules = original_modules
                    
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
                'error': log_capture.getvalue() if not success else '',
                'temp_dir': temp_dir_path,  # Non-null if using temp mode
                'output_dir': used_output_dir
            })

        @self.app.route('/api/download_generated_zip')
        def download_generated_zip():
            """Download generated files as a ZIP archive."""
            import zipfile
            import io
            import shutil
            from flask import send_file
            
            source_dir = request.args.get('source_dir')
            
            if not source_dir or not os.path.isdir(source_dir):
                return jsonify({'error': 'Invalid source directory'}), 400
            
            # Security check: only allow temp directories
            if not source_dir.startswith(os.path.join(os.sep, 'tmp')) and '/tmp' not in source_dir:
                return jsonify({'error': 'Only temporary directories can be downloaded'}), 403
            
            try:
                # Create ZIP in memory
                memory_file = io.BytesIO()
                with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in os.walk(source_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_dir)
                            zf.write(file_path, arcname)
                
                memory_file.seek(0)
                
                # Cleanup temp directory after zipping
                try:
                    shutil.rmtree(source_dir)
                except Exception:
                    pass  # Ignore cleanup errors
                
                return send_file(
                    memory_file,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name='axion_generated.zip'
                )
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/run_check')
        def run_gui_check():
            import io
            from contextlib import redirect_stdout

            log_capture = io.StringIO()
            with redirect_stdout(log_capture):
                print("Starting Design Rule Check...")
                print("Using current analysis state...")
                
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

                # Inject parsing errors from modules (to match index() behavior)
                for m in self.axion.analyzed_modules:
                    if 'parsing_errors' in m:
                        for err in m['parsing_errors']:
                            self.checker._add_error("Parsing Error", m['name'], err.get('msg', 'Unknown parsing error'))

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

        @self.app.route('/api/analysis_status')
        def analysis_status():
            """Return current analysis status"""
            return jsonify({
                'is_analyzing': self.analysis_cache.is_analyzing,
                'last_analysis_time': self.analysis_cache.last_analysis_time,
                'module_count': len(self.axion.analyzed_modules),
                'error': self.analysis_error,
                'file_watcher_active': self.file_observer is not None and self.file_observer.is_alive() if self.file_observer else False
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

        @self.app.route('/source')
        def view_source():
            """View source file with syntax highlighting"""
            filepath = request.args.get('file', '')
            
            if not filepath:
                return "No file specified", 400
            
            if not os.path.exists(filepath):
                return f"File not found: {filepath}", 404
            
            # Security: Only allow viewing files within known source directories
            # or files that are in the analyzed modules
            allowed = False
            all_dirs = (
                self.axion.src_dirs + self.axion.xml_src_dirs + 
                self.axion.yaml_src_dirs + self.axion.json_src_dirs
            )
            all_files = (
                self.axion.src_files + self.axion.xml_src_files +
                self.axion.yaml_src_files + self.axion.json_src_files
            )
            
            # Check if file is in a known directory
            for d in all_dirs:
                if filepath.startswith(os.path.abspath(d)):
                    allowed = True
                    break
            
            # Check if file is explicitly listed
            if filepath in all_files or os.path.abspath(filepath) in [os.path.abspath(f) for f in all_files]:
                allowed = True
            
            # Check if file belongs to an analyzed module
            for m in self.axion.analyzed_modules:
                if m.get('file') == filepath or os.path.abspath(m.get('file', '')) == os.path.abspath(filepath):
                    allowed = True
                    break
            
            if not allowed:
                return "Access denied: File not in source paths", 403
            
            # Read file content
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return f"Error reading file: {e}", 500
            
            # Determine file type
            ext = os.path.splitext(filepath)[1].lower()
            file_type_map = {
                '.vhd': 'VHDL',
                '.vhdl': 'VHDL',
                '.json': 'JSON',
                '.yaml': 'YAML',
                '.yml': 'YAML',
                '.xml': 'XML'
            }
            file_type = file_type_map.get(ext, 'Text')
            filename = os.path.basename(filepath)
            
            return render_template('source_viewer.html',
                                   filepath=filepath,
                                   filename=filename,
                                   file_type=file_type,
                                   content=content)

        @self.app.route('/api/source/save', methods=['POST'])
        def save_source():
            """Save edited source file"""
            try:
                data = request.json
                filepath = data.get('filepath', '')
                content = data.get('content', '')
                
                if not filepath:
                    return jsonify({'success': False, 'error': 'No file specified'})
                
                if not os.path.exists(filepath):
                    return jsonify({'success': False, 'error': 'File not found'})
                
                # Security: Same checks as view_source
                allowed = False
                all_dirs = (
                    self.axion.src_dirs + self.axion.xml_src_dirs + 
                    self.axion.yaml_src_dirs + self.axion.json_src_dirs
                )
                all_files = (
                    self.axion.src_files + self.axion.xml_src_files +
                    self.axion.yaml_src_files + self.axion.json_src_files
                )
                
                for d in all_dirs:
                    if filepath.startswith(os.path.abspath(d)):
                        allowed = True
                        break
                
                if filepath in all_files or os.path.abspath(filepath) in [os.path.abspath(f) for f in all_files]:
                    allowed = True
                
                for m in self.axion.analyzed_modules:
                    if m.get('file') == filepath or os.path.abspath(m.get('file', '')) == os.path.abspath(filepath):
                        allowed = True
                        break
                
                if not allowed:
                    return jsonify({'success': False, 'error': 'Access denied: File not in source paths'})
                
                # Write file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Trigger re-analysis to pick up changes
                try:
                    self.axion.analyzed_modules = []
                    self.axion.is_analyzed = False
                    self.axion.analyze()
                except:
                    pass  # Don't fail if analysis has issues
                
                return jsonify({'success': True})
            except Exception as e:
                import traceback
                return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

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

    def _background_analyze(self):
        """Run analysis in background thread"""
        import os as os_module

        # Check if already analyzing
        if self.analysis_cache.is_analyzing:
            return

        # Check if refresh is actually needed
        if not self.analysis_cache.needs_refresh(self.axion):
            return

        with self.analysis_cache.analysis_lock:
            if self.analysis_cache.is_analyzing:
                return  # Already analyzing

            self.analysis_cache.is_analyzing = True

        try:
            # Silent analysis - no prints
            import io
            from contextlib import redirect_stdout

            # Keep old modules in case of parse errors
            old_modules = self.axion.analyzed_modules[:]

            with redirect_stdout(io.StringIO()):
                self.axion.analyzed_modules = []
                self.axion.is_analyzed = False

                try:
                    self.axion.analyze()
                except Exception:
                    # If analysis fails completely, restore old modules
                    if not self.axion.analyzed_modules:
                        self.axion.analyzed_modules = old_modules
                    # Continue with whatever modules we have

            # Run rule checks
            from axion_hdl.rule_checker import RuleChecker
            self.checker = RuleChecker()
            self.checker.run_all_checks(self.axion.analyzed_modules)

            # Inject parsing errors
            for m in self.axion.analyzed_modules:
                if 'parsing_errors' in m:
                    for err in m['parsing_errors']:
                        self.checker._add_error("Parsing Error", m['name'], err.get('msg', 'Unknown parsing error'))

            if hasattr(self.axion, 'parse_errors') and self.axion.parse_errors:
                for err in self.axion.parse_errors:
                    fname = os_module.path.basename(err.get('file', 'unknown_file'))
                    self.checker._add_error("Format Error", fname, err.get('msg', 'Unknown error'))

            # Build module status map and attach to modules
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

            # Update cache
            self.analysis_cache.update_mtimes(self.axion)
            self.analysis_error = None

        except Exception as e:
            self.analysis_error = str(e)

        finally:
            self.analysis_cache.is_analyzing = False

    def _start_file_watcher(self):
        """Start file system watcher for source files"""
        if not WATCHDOG_AVAILABLE:
            return

        try:
            all_dirs = (
                self.axion.src_dirs +
                self.axion.xml_src_dirs +
                self.axion.yaml_src_dirs +
                self.axion.json_src_dirs
            )

            if not all_dirs:
                return

            event_handler = SourceFileEventHandler(self)
            self.file_observer = Observer()

            for directory in all_dirs:
                if os.path.exists(directory):
                    self.file_observer.schedule(event_handler, directory, recursive=True)

            self.file_observer.start()

        except Exception as e:
            pass  # Silent fail

    def run(self, port=None):
        self.setup_app()
        if port is not None:
            self.port = port
        url = f"http://127.0.0.1:{self.port}"
        print(f"Starting Axion GUI at {url}")

        # Open browser automatically
        webbrowser.open(url)

        try:
            # Run Flask app
            # Only enable debug/reloader if requested via CLI flag
            self.app.run(port=self.port, debug=self.debug_mode, use_reloader=self.debug_mode)
        finally:
            # Cleanup file watcher
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()

    # --- Platform Selection Helpers (Moved from setup_app) ---

    def _select_folder_macos(self):
            import subprocess
            script = '''
            tell application "System Events"
                activate
                set folderPath to POSIX path of (choose folder with prompt "Select Source Directory")
            end tell
            '''
            try:
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return jsonify({'path': result.stdout.strip()})
                return jsonify({'error': 'User cancelled', 'path': ''})
            except subprocess.TimeoutExpired:
                return jsonify({'error': 'Selection timed out', 'path': ''})


    def _select_file_macos(self):
            import subprocess
            script = '''
            tell application "System Events"
                activate
                set filePath to POSIX path of (choose file with prompt "Select Source File" of type {"vhd", "vhdl", "json", "yaml", "yml", "xml"})
            end tell
            '''
            try:
                result = subprocess.run(['osascript', '-e', script], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return jsonify({'path': result.stdout.strip()})
                return jsonify({'error': 'User cancelled', 'path': ''})
            except subprocess.TimeoutExpired:
                return jsonify({'error': 'Selection timed out', 'path': ''})


    def _select_folder_windows(self):
            import subprocess
            # PowerShell command to open FolderBrowserDialog
            ps_script = """
            Add-Type -AssemblyName System.Windows.Forms
            $f = New-Object System.Windows.Forms.FolderBrowserDialog
            $f.ShowNewFolderButton = $true
            $f.Description = "Select Source Directory"
            if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Host $f.SelectedPath
            }
            """
            try:
                result = subprocess.run(["powershell", "-Command", ps_script], 
                                      capture_output=True, text=True, timeout=60)
                path = result.stdout.strip()
                if path and os.path.exists(path):
                    return jsonify({'path': path})
                return jsonify({'error': 'User cancelled', 'path': ''})
            except Exception as e:
                return jsonify({'error': f'Windows selection failed: {str(e)}', 'path': ''})


    def _select_file_windows(self):
            import subprocess
            # PowerShell command to open OpenFileDialog
            ps_script = """
            Add-Type -AssemblyName System.Windows.Forms
            $f = New-Object System.Windows.Forms.OpenFileDialog
            $f.Filter = "HDL & Config Files (*.vhd;*.vhdl;*.json;*.yaml;*.yml;*.xml)|*.vhd;*.vhdl;*.json;*.yaml;*.yml;*.xml|All Files (*.*)|*.*"
            if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
                Write-Host $f.FileName
            }
            """
            try:
                result = subprocess.run(["powershell", "-Command", ps_script], 
                                      capture_output=True, text=True, timeout=60)
                path = result.stdout.strip()
                if path and os.path.exists(path):
                    return jsonify({'path': path})
                return jsonify({'error': 'User cancelled', 'path': ''})
            except Exception as e:
                return jsonify({'error': f'Windows selection failed: {str(e)}', 'path': ''})


    def _select_folder_linux(self):
            import subprocess
            import shutil
            
            # 1. Try zenity (GNOME/GTK)
            if shutil.which('zenity'):
                try:
                    result = subprocess.run(['zenity', '--file-selection', '--directory', '--title=Select Source Directory'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return jsonify({'path': result.stdout.strip()})
                    return jsonify({'error': 'User cancelled', 'path': ''})
                except:
                    pass # Fallback
            
            # 2. Try kdialog (KDE)
            if shutil.which('kdialog'):
                try:
                    result = subprocess.run(['kdialog', '--getexistingdirectory'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return jsonify({'path': result.stdout.strip()})
                    return jsonify({'error': 'User cancelled', 'path': ''})
                except:
                    pass

            return jsonify({'error': 'No suitable file dialog tool found (install zenity or kdialog)', 'path': ''})


    def _select_file_linux(self):
            import subprocess
            import shutil
            
            # 1. Try zenity
            if shutil.which('zenity'):
                try:
                    # Zenity file filter syntax: --file-filter="Name | *.vhd *.vhdl"
                    result = subprocess.run(['zenity', '--file-selection', '--title=Select Source File', 
                                           '--file-filter=HDL & Config | *.vhd *.vhdl *.json *.yaml *.yml *.xml'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return jsonify({'path': result.stdout.strip()})
                    return jsonify({'error': 'User cancelled', 'path': ''})
                except:
                    pass
            
            # 2. Try kdialog
            if shutil.which('kdialog'):
                try:
                    # KDialog syntax: "extension1 extension2"
                    result = subprocess.run(['kdialog', '--getopenfilename', '.', 
                                           '*.vhd *.vhdl *.json *.yaml *.yml *.xml'], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return jsonify({'path': result.stdout.strip()})
                    return jsonify({'error': 'User cancelled', 'path': ''})
                except:
                    pass

            return jsonify({'error': 'No suitable file dialog tool found (install zenity or kdialog)', 'path': ''})

    def _read_version(self):
        """
        Return a random version number to force cache busting on every restart.
        This ensures CSS/JS updates are always reflected immediately.
        """
        import random
        return str(random.randint(1000, 9999))


def start_gui(axion_instance, port=5000, debug_mode=False):
    gui = AxionGUI(axion_instance, debug_mode=debug_mode)
    gui.port = port
    gui.run()
