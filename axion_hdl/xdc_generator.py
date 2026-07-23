"""
Axion HDL XDC Constraint Generator Module

This module generates Xilinx Design Constraints (XDC) files for the
generated AXI4-Lite register interface modules (*_axion_reg).

XDC files are only generated for CDC-enabled modules (CDC_EN). Axion-HDL
always synchronizes CDC-enabled register signals and strobes through its
own internally-generated synchronizer chain, so the exact internal
crossing point (source register/port -> the first synchronizer stage) is
known and can be false-pathed precisely:

- RO registers/fields: the module-side input port drives the first
  synchronizer stage in the axi_aclk domain ->
  `set_false_path -from <port> -to <first stage>`.
- RW/WO registers/fields: the AXI-domain storage register `<name>_reg`
  drives the first synchronizer stage in the module_clk domain ->
  `set_false_path -from <name>_reg -to <first stage>`.
- Read/write strobes: the axi_aclk-domain toggle register `<name>_rd/wr_toggle`
  drives the first stage of its own synchronizer chain in the module_clk
  domain -> same pattern, targeting the toggle crossing only. The
  regenerated single-cycle pulse on the actual `<name>_rd/wr_strobe` port
  is a normal, fully-synchronized module_clk-domain signal and needs no
  exception.

Only the first synchronizer stage is targeted: subsequent stages
(stage0 -> stage1 -> ... ) are same-clock-domain register-to-register
hops that standard timing analysis already checks correctly, so no
exception is needed (or wanted) for them.

VHDLGenerator and SystemVerilogGenerator both name the first synchronizer
stage the same way: discrete signals `<name>_sync0`, `<name>_sync1`, ...
(SystemVerilogGenerator previously declared these as an unpacked array
`<name>_sync[N]`, which required XDCGenerator to special-case the SV
backend's cell-name pattern - see PR #130 and the follow-up fix that
switched SV to the same discrete-signal convention as VHDL. XDCGenerator
no longer needs to know which backend it targets for cell-naming
purposes; the `backend` constructor parameter is kept only to pick the
output file suffix, so `--vhdl --systemverilog --xdc` runs still produce
two distinct files instead of one overwriting the other.)

CDC-disabled modules have no internal synchronizer to scope a false path
to - the register signals are single-clock-domain internally, and any
crossing would happen entirely outside axion_reg, in logic Axion-HDL
cannot see. Generating a blanket false path there would be unscoped and
unsafe (it would silently exempt real same-clock-domain timing paths in
the user's downstream logic), so no XDC file is produced for these
modules.

The constraints are instance-independent: instead of hard-coding an
instance path (which is chosen by the user, not by Axion-HDL), cells are
located through their module reference name:

    get_cells -hierarchical -filter {REF_NAME == <module>_axion_reg ||
                                     ORIG_REF_NAME == <module>_axion_reg}

This matches every instance of the module anywhere in the design
hierarchy, regardless of the instance names chosen by the integrator.
Vivado keeps ORIG_REF_NAME intact even when synthesis renames or uniquifies
the module, so the constraints survive hierarchy rebuilding.
"""

import os


class XDCGenerator:
    """Generates Xilinx XDC timing constraint files for CDC-enabled register modules."""

    def __init__(self, output_dir, backend='vhdl'):
        """
        Initialize XDC generator.

        Args:
            output_dir: Directory where generated .xdc files are written
            backend: Which HDL backend the constraints are generated for -
                     'vhdl' (default) or 'systemverilog'. Both backends
                     declare the first CDC synchronizer stage under the
                     same discrete signal name (`<name>_sync0`), so this
                     no longer affects the constraint cell-name patterns.
                     It only selects the output file suffix (see
                     generate_xdc()), so generating XDC for both backends
                     in the same output directory produces two distinct
                     files instead of one overwriting the other.
        """
        self.output_dir = output_dir
        if backend not in ('vhdl', 'systemverilog'):
            raise ValueError(
                f"XDCGenerator: unknown backend {backend!r}, expected "
                f"'vhdl' or 'systemverilog'")
        self.backend = backend

    def generate_xdc(self, module_data):
        """
        Generate the XDC constraint file for a single module.

        Only CDC-enabled modules produce a file - see module docstring for
        why CDC-disabled modules are skipped.

        Args:
            module_data: Parsed module dictionary (same structure consumed
                         by VHDLGenerator/SystemVerilogGenerator)

        Returns:
            Path of the generated .xdc file, or None if the module has CDC
            disabled (no file is written).

        Note on file naming: the VHDL backend (the original/default XDC
        target) keeps the plain `<module>_axion_reg.xdc` name for backward
        compatibility with existing projects and tests. The SystemVerilog
        backend writes `<module>_axion_reg_sv.xdc` instead, so generating
        XDC for both backends in the same output directory (e.g. a
        `--vhdl --systemverilog --xdc` run) produces two distinct files
        rather than the second silently overwriting the first.
        """
        if not module_data.get('cdc_enabled'):
            return None

        module_name = module_data['name']
        entity_name = f"{module_name}_axion_reg"
        file_suffix = '_sv' if self.backend == 'systemverilog' else ''

        lines = self._generate_header(module_data, entity_name)
        lines.extend(self._generate_cell_lookup(entity_name))
        lines.extend(self._generate_register_constraints(module_data))
        lines.extend(self._generate_packed_register_constraints(module_data))
        lines.extend(self._generate_strobe_constraints(module_data))

        output_path = os.path.join(self.output_dir, f"{entity_name}{file_suffix}.xdc")
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

        return output_path

    # ------------------------------------------------------------------
    # Section generators
    # ------------------------------------------------------------------

    def _generate_header(self, module_data, entity_name):
        """Generate the file header with usage notes."""
        from axion_hdl import __version__

        backend_label = 'SystemVerilog' if self.backend == 'systemverilog' else 'VHDL'
        return [
            "#" * 78,
            f"# {entity_name}.xdc",
            f"# Timing constraints for the {entity_name} AXI4-Lite register interface",
            f"# Target HDL backend: {backend_label}",
            "#",
            f"# Generated by Axion-HDL v{__version__}",
            "#",
            "# This file is INSTANCE-INDEPENDENT: cells are located via their module",
            "# reference name (REF_NAME / ORIG_REF_NAME), so the constraints apply to",
            "# every instance of the module anywhere in the design hierarchy, no",
            "# matter which instance names the integrator chose.",
            "#",
            "# Every exception below is scoped to a single CDC crossing hop: from the",
            "# source-domain register/port to the first stage of Axion-HDL's own",
            "# synchronizer chain. Nothing downstream of the synchronized output",
            "# ports/strobes is touched, so normal same-clock-domain timing analysis",
            "# still applies to all consuming logic.",
            "#",
            "# Usage:",
            "#   Add this file to the Vivado project as a normal constraint file",
            "#   (add_files / read_xdc). It must be processed together with (or",
            "#   after) the constraints that create the design clocks.",
            "#",
            "# Note: if the module is not (yet) instantiated in the design, Vivado",
            "# reports 'no valid object(s) found' critical warnings for these",
            "# constraints. They are harmless and disappear once the module is",
            "# instantiated.",
            "#" * 78,
            "",
        ]

    def _generate_cell_lookup(self, entity_name):
        """Generate the instance-independent cell lookup."""
        return [
            "# Locate every instance of the register module (instance-name agnostic).",
            "# ORIG_REF_NAME keeps matching when synthesis renames/uniquifies the module.",
            f"set axion_cells [get_cells -hierarchical -filter {{REF_NAME == {entity_name} || ORIG_REF_NAME == {entity_name}}}]",
            "",
        ]

    def _generate_register_constraints(self, module_data):
        """Generate false-path constraints for standalone (non-packed) registers."""
        lines = []
        for reg in module_data.get('registers', []):
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] == 'RO':
                lines.extend(self._cdc_crossing_constraint(
                    from_port=reg['signal_name'],
                    sync_base=reg['signal_name'],
                    access_mode='RO',
                    description=reg.get('description', '')))
            else:
                lines.extend(self._cdc_crossing_constraint(
                    from_cell=f"{reg['signal_name']}_reg",
                    from_cell_wide_ok=True,
                    sync_base=reg['signal_name'],
                    access_mode=reg['access_mode'],
                    description=reg.get('description', '')))
        return lines

    def _generate_packed_register_constraints(self, module_data):
        """Generate false-path constraints for packed register fields."""
        lines = []
        for packed_reg in module_data.get('packed_registers', []):
            writable_fields = [f for f in packed_reg.get('fields', [])
                                if f['access_mode'] in ('RW', 'WO')]
            ro_fields = [f for f in packed_reg.get('fields', [])
                         if f['access_mode'] == 'RO']

            for field in ro_fields:
                sig_name = f"{packed_reg['reg_name']}_{field['name']}"
                lines.extend(self._cdc_crossing_constraint(
                    from_port=sig_name,
                    sync_base=sig_name,
                    access_mode='RO',
                    description=field.get('description', '')))

            # All writable fields of a packed register share one storage
            # word (<reg_name>_reg) and one synchronizer chain - one
            # constraint per packed register, not per field.
            if writable_fields:
                field_names = ', '.join(f['name'] for f in writable_fields)
                lines.extend(self._cdc_crossing_constraint(
                    from_cell=f"{packed_reg['reg_name']}_reg",
                    sync_base=f"{packed_reg['reg_name']}_reg",
                    access_mode='RW/WO',
                    description=f"packed storage for fields: {field_names}"))
        return lines

    def _generate_strobe_constraints(self, module_data):
        """
        Generate false-path constraints for the toggle-synchronizer CDC of
        read/write strobes (see module docstring). Only the toggle
        register's crossing into its first sync stage is constrained; the
        regenerated pulse on the actual strobe port is a normal
        module_clk-domain signal and needs no exception.
        """
        lines = []
        for reg in module_data.get('registers', []):
            if reg.get('is_packed'):
                continue
            if reg.get('read_strobe'):
                lines.extend(self._toggle_crossing_constraint(reg['signal_name'], 'rd'))
            if reg.get('write_strobe'):
                lines.extend(self._toggle_crossing_constraint(reg['signal_name'], 'wr'))
        for pr in module_data.get('packed_registers', []):
            if pr.get('read_strobe'):
                lines.extend(self._toggle_crossing_constraint(pr['reg_name'], 'rd'))
            if pr.get('write_strobe'):
                lines.extend(self._toggle_crossing_constraint(pr['reg_name'], 'wr'))
        return lines

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sync_stage0_filter(self, sync_base):
        """
        Build the `NAME =~` filter alternatives that match the first CDC
        synchronizer stage cell for `sync_base`.

        Both VHDLGenerator and SystemVerilogGenerator declare discrete
        signals `<sync_base>_sync0`, `<sync_base>_sync1`, ... (and
        `<sync_base>0_sync0`, `<sync_base>1_sync0`, ... for chunks of
        VHDL registers wider than 32 bits) - see generator.py and
        systemverilog_generator.py.
        """
        return (f"{{NAME =~ */{sync_base}_sync0 || "
                f"NAME =~ */{sync_base}[0-9]*_sync0}}")

    def _cdc_crossing_constraint(self, sync_base, access_mode, description="",
                                  from_port=None, from_cell=None,
                                  from_cell_wide_ok=False):
        """
        Build a false-path constraint scoped to one CDC crossing hop: from
        the source-domain register/port to the D input of the first
        synchronizer stage.

        Exactly one of from_port/from_cell must be given:
        - from_port: a top-level port pin of the module (RO register/field
          inputs). Matched via get_pins with vector-bit coverage.
        - from_cell: an internal storage register (RW/WO). Matched via
          get_cells. When from_cell_wide_ok is set, also matches the
          `<from_cell>0`, `<from_cell>1`, ... chunks used for registers
          wider than 32 bits.

        The `-to` side always targets the first synchronizer stage via
        get_cells - the first synchronizer stage is always an internal
        register, never a port. See _sync_stage0_filter() for the exact
        cell-name pattern.
        """
        if access_mode == 'RO':
            comment_dir = 'module -> AXI, axi_aclk-domain sync stage 0'
        else:
            comment_dir = 'AXI -> module, module_clk-domain sync stage 0'

        desc = f" - {description}" if description else ""
        lines = [f"# {sync_base} ({access_mode}, {comment_dir}){desc}"]

        if from_port is not None:
            from_expr = (f"[get_pins -of_objects $axion_cells -filter "
                         f"{{NAME =~ */{from_port} || NAME =~ */{from_port}[*]}}]")
        else:
            if from_cell_wide_ok:
                from_filter = (f"{{NAME =~ */{from_cell} || "
                               f"NAME =~ */{from_cell}[0-9]*}}")
            else:
                from_filter = f"{{NAME =~ */{from_cell}}}"
            from_expr = f"[get_cells -of_objects $axion_cells -filter {from_filter}]"

        to_filter = self._sync_stage0_filter(sync_base)
        to_expr = f"[get_cells -of_objects $axion_cells -filter {to_filter}]"

        lines.append(f"set_false_path -from {from_expr} -to {to_expr}")
        lines.append("")
        return lines

    def _toggle_crossing_constraint(self, name, direction):
        """
        Build a false-path constraint for a strobe's toggle-synchronizer
        crossing: from `<name>_<direction>_toggle` (source domain) to the
        first stage of its synchronizer chain (destination domain). See
        _sync_stage0_filter() for the exact cell-name pattern.
        """
        base = f"{name}_{direction}_toggle"
        kind = 'read strobe' if direction == 'rd' else 'write strobe'
        to_filter = self._sync_stage0_filter(base)
        return [
            f"# {name} {kind} toggle CDC (axi_aclk -> module_clk)",
            f"set_false_path -from [get_cells -of_objects $axion_cells -filter "
            f"{{NAME =~ */{base}}}] -to [get_cells -of_objects $axion_cells "
            f"-filter {to_filter}]",
            "",
        ]
