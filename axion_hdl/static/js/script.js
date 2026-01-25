/**
 * Axion-HDL Website Scripts
 * Interactive demo and UI features
 */

// Default code samples for each format
const defaultSamples = {
    yaml: `module: spi_master
base_addr: "0x0000"
config:
  cdc_en: true

registers:
  - name: control
    addr: "0x00"
    access: RW
    w_strobe: true
    description: "SPI control register"

  - name: status
    addr: "0x04"
    access: RO
    r_strobe: true
    description: "SPI status register"`,

    vhdl: `-- @axion_def BASE_ADDR=0x0000 CDC_EN

library ieee;
use ieee.std_logic_1164.all;

entity spi_master is
    port (
        clk : in std_logic;
        rst : in std_logic
    );
end entity spi_master;

architecture rtl of spi_master is
    -- Control register
    signal control : std_logic_vector(31 downto 0);
    -- @axion RW W_STROBE DESC="SPI control register"
    
    -- Status register
    signal status : std_logic_vector(31 downto 0);
    -- @axion RO R_STROBE DESC="SPI status register"
begin
    -- Implementation here
end architecture rtl;`,

    xml: `<?xml version="1.0" encoding="UTF-8"?>
<register_map module="spi_master" base_addr="0x0000">
    <config cdc_en="true"/>
    
    <register name="control" addr="0x00" 
              access="RW" w_strobe="true"
              description="SPI control register"/>
              
    <register name="status" addr="0x04"
              access="RO" r_strobe="true"
              description="SPI status register"/>
</register_map>`,

    json: `{
    "module": "spi_master",
    "base_addr": "0x0000",
    "config": {
        "cdc_en": true
    },
    "registers": [
        {
            "name": "control",
            "addr": "0x00",
            "access": "RW",
            "w_strobe": true,
            "description": "SPI control register"
        },
        {
            "name": "status",
            "addr": "0x04",
            "access": "RO",
            "r_strobe": true,
            "description": "SPI status register"
        }
    ]
}`
};

// State
let currentFormat = 'yaml';
let generatedFiles = [];
let vhdlContent = '';

document.addEventListener('DOMContentLoaded', function () {
    // Initialize demo editor
    initDemo();

    // Copy to clipboard
    initCopyButtons();

    // Mobile menu
    initMobileMenu();

    // Scroll animations
    initScrollAnimations();

    // Smooth scroll for anchor links
    initSmoothScroll();
});

/**
 * Initialize interactive demo
 */
function initDemo() {
    const editor = document.getElementById('editor');
    const tabs = document.querySelectorAll('.demo-tab');
    const outputTabs = document.querySelectorAll('.output-tab');
    const generateBtn = document.getElementById('generate-btn');
    const resetBtn = document.getElementById('reset-btn');
    const downloadVhdl = document.getElementById('download-vhdl');
    const downloadAll = document.getElementById('download-all');

    if (!editor) return;

    // Load initial sample
    editor.value = defaultSamples[currentFormat];

    // Input format tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const format = tab.dataset.format;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update editor content
            currentFormat = format;
            editor.value = defaultSamples[format];

            // Reset terminal
            resetTerminal();
        });
    });

    // Output tab switching (Terminal / VHDL)
    outputTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const output = tab.dataset.output;

            // Update active tab
            outputTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show corresponding panel
            document.querySelectorAll('.output-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(`${output}-panel`)?.classList.add('active');
        });
    });

    // Generate button
    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerate);
    }

    // Reset button
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            editor.value = defaultSamples[currentFormat];
            resetTerminal();
        });
    }

    // Download VHDL
    if (downloadVhdl) {
        downloadVhdl.addEventListener('click', () => {
            if (vhdlContent) {
                downloadFile('generated.vhd', vhdlContent);
            }
        });
    }

    // Download all files
    if (downloadAll) {
        downloadAll.addEventListener('click', () => {
            generatedFiles.forEach(file => {
                downloadFile(file.name, file.content);
            });
        });
    }
}

/**
 * Handle generate button click
 */
async function handleGenerate() {
    const editor = document.getElementById('editor');
    const generateBtn = document.getElementById('generate-btn');
    const terminalOutput = document.getElementById('terminal-output');
    const vhdlOutput = document.getElementById('vhdl-output');
    const downloadSection = document.getElementById('download-section');

    const content = editor.value.trim();

    if (!content) {
        showTerminalOutput('❌ Error: Please enter some content first.');
        return;
    }

    // Show loading state
    generateBtn.classList.add('loading');
    generateBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
        </svg>
        Generating...
    `;

    // Reset download section and VHDL output
    downloadSection.style.display = 'none';
    if (vhdlOutput) {
        vhdlOutput.innerHTML = `<pre><code><span class="dim">Generating VHDL...</span></code></pre>`;
    }

    // Show initial command
    showTerminalOutput(`$ axion-hdl -s input.${getExtension(currentFormat)} -o output/ --all\n\nGenerating...`);

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format: currentFormat,
                content: content
            })
        });

        const data = await response.json();

        // Display terminal output
        showTerminalOutput(data.terminal || 'No output');

        if (data.success) {
            // Store generated files
            generatedFiles = data.files || [];
            vhdlContent = data.vhdl || '';

            // Show download section and VHDL output
            if (vhdlContent) {
                downloadSection.style.display = 'flex';

                // Display VHDL in viewer with basic syntax highlighting
                if (vhdlOutput) {
                    const highlighted = highlightVHDL(vhdlContent);
                    vhdlOutput.innerHTML = `<pre><code>${highlighted}</code></pre>`;
                }

                // Switch to VHDL tab automatically
                document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
                document.querySelector('.output-tab[data-output="vhdl"]')?.classList.add('active');
                document.querySelectorAll('.output-panel').forEach(p => p.classList.remove('active'));
                document.getElementById('vhdl-panel')?.classList.add('active');
            }
        } else {
            if (vhdlOutput) {
                vhdlOutput.innerHTML = `<pre><code><span class="error">❌ Generation failed. Check terminal for details.</span></code></pre>`;
            }
        }

    } catch (error) {
        showTerminalOutput(`❌ Error: ${error.message || 'Failed to connect to server'}`);
        if (vhdlOutput) {
            vhdlOutput.innerHTML = `<pre><code><span class="error">❌ Connection error</span></code></pre>`;
        }
    }

    // Reset button state
    generateBtn.classList.remove('loading');
    generateBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        Generate
    `;
}

/**
 * Basic VHDL syntax highlighting
 */
function highlightVHDL(code) {
    const keywords = ['library', 'use', 'entity', 'architecture', 'is', 'of', 'begin', 'end', 'port', 'generic',
        'signal', 'variable', 'constant', 'type', 'subtype', 'if', 'then', 'else', 'elsif',
        'case', 'when', 'for', 'loop', 'while', 'process', 'function', 'procedure', 'package',
        'component', 'map', 'in', 'out', 'inout', 'buffer', 'downto', 'to', 'others', 'all',
        'rising_edge', 'falling_edge', 'and', 'or', 'not', 'xor', 'nand', 'nor', 'std_logic',
        'std_logic_vector', 'unsigned', 'signed', 'integer', 'natural', 'positive', 'boolean'];

    return code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/(--.*$)/gm, '<span class="comment">$1</span>')
        .replace(/"([^"]*)"/g, '<span class="string">"$1"</span>')
        .replace(/'([^']*)'/g, '<span class="string">\'$1\'</span>')
        .replace(new RegExp(`\\b(${keywords.join('|')})\\b`, 'gi'), '<span class="keyword">$1</span>');
}

/**
 * Show output in terminal
 */
function showTerminalOutput(text) {
    const terminalOutput = document.getElementById('terminal-output');
    if (terminalOutput) {
        // Convert text to styled HTML
        const html = text
            .replace(/✓/g, '<span class="success">✓</span>')
            .replace(/❌/g, '<span class="error">❌</span>')
            .replace(/⚠️/g, '<span class="warning">⚠️</span>')
            .replace(/→/g, '<span class="success">→</span>')
            .replace(/\$ (.*)/g, '<span class="prompt">$</span> $1');

        terminalOutput.innerHTML = `<pre><code>${html}</code></pre>`;
    }
}

/**
 * Reset terminal to initial state
 */
function resetTerminal() {
    const terminalOutput = document.getElementById('terminal-output');
    const downloadSection = document.getElementById('download-section');

    if (terminalOutput) {
        terminalOutput.innerHTML = `<pre><code><span class="dim">Click "Generate" to run axion-hdl...</span></code></pre>`;
    }

    if (downloadSection) {
        downloadSection.style.display = 'none';
    }

    generatedFiles = [];
    vhdlContent = '';
}

/**
 * Get file extension for format
 */
function getExtension(format) {
    const ext = { yaml: 'yaml', vhdl: 'vhd', xml: 'xml', json: 'json' };
    return ext[format] || 'txt';
}

/**
 * Download file
 */
function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Copy to clipboard functionality
 */
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const textToCopy = button.dataset.copy;

            try {
                await navigator.clipboard.writeText(textToCopy);

                button.classList.add('copied');
                button.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                `;

                setTimeout(() => {
                    button.classList.remove('copied');
                    button.innerHTML = `
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                        </svg>
                    `;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });
}

/**
 * Mobile menu toggle
 */
function initMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuBtn.classList.toggle('active');
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                menuBtn.classList.remove('active');
            });
        });
    }
}

/**
 * Scroll-triggered animations
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card, .mode-card, .stat-item').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Navbar background on scroll
 */
window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.style.background = window.scrollY > 50
            ? 'rgba(10, 14, 20, 0.98)'
            : 'rgba(10, 14, 20, 0.9)';
    }
});
