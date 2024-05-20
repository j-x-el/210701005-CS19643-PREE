# Kurono Runner

This script is designed to run the Kurono project, providing options for different build targets and testing configurations.

## Prerequisites

- Python 3.x
- Docker (if you intend to use Docker containers)
- Node.js and Cypress (if you intend to run Cypress tests)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/your-repo/kurono.git
    cd kurono
    ```

2. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Ensure Docker is installed and running if you plan to use Docker containers.

## Usage

The script provides several command-line options to customize the build and testing process.

### Options

- `-t`, `--target`:
  - Specify the build stage you wish the Docker containers to stop at.
  - Options: `runner`, `tester`
  - Default: `runner`
  - Example: `python run_kurono.py --target tester`

- `-c`, `--using-cypress`:
  - Specify if you want to run the project for running Cypress tests.
  - This disables the building of the Docker images and builds the frontend in production mode without watching for changes.
  - Default: `False`
  - Example: `python run_kurono.py --using-cypress`

### Examples

1. Run the project with the default settings:

    ```sh
    python run_kurono.py
    ```

2. Run the project for testing purposes:

    ```sh
    python run_kurono.py --target tester
    ```

3. Run the project with Cypress tests enabled:

    ```sh
    python run_kurono.py --using-cypress
    ```

## Logging

The script uses Python's built-in logging module to provide basic logging functionality. Logs will be printed to the console.

## Troubleshooting

If an error occurs, the script will print the traceback to help diagnose the issue. Ensure all dependencies are installed and that Docker is running if required.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Contact

For any questions or issues, please contact the maintainer at [maintainer@example.com].
