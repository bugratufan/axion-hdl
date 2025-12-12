# Developer Guide

## Project Structure

```
axion-hdl/
├── axion_hdl/          # Main package
│   ├── axion.py        # Core AxionHDL class
│   ├── cli.py          # Command-line interface
│   ├── parser.py       # VHDL parser
│   └── generators/     # Output generators
├── tests/              # Test suite
└── docs/               # Documentation
```

## Running Tests

```bash
make test
```

## Contributing

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes
4. Run tests: `make test`
5. Submit a PR to `develop`
