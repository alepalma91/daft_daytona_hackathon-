import os
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

# Load environment variables
# Try to load from project root first, then current directory
from pathlib import Path
env_path = Path(__file__).parent.parent.parent / '.env'
if not env_path.exists():
    load_dotenv()  # Try default locations
else:
    load_dotenv(env_path)

# Define the configuration from environment
api_key = os.getenv("DAYTONA_API_KEY")
if not api_key:
    raise ValueError("DAYTONA_API_KEY not found in environment variables. Please set it in your .env file.")

# Build config with optional parameters
config_params = {
    'api_key': api_key
}

# Add optional parameters if they exist
if api_url := os.getenv('DAYTONA_API_URL'):
    config_params['api_url'] = api_url
    
if timeout := os.getenv('DAYTONA_TIMEOUT'):
    config_params['timeout'] = int(timeout)

config = DaytonaConfig(**config_params)

# Initialize the Daytona client
daytona = Daytona(config)

# Create the Sandbox instance with optional resource limits
sandbox_params = {}

# Add optional sandbox parameters if they exist
if max_runtime := os.getenv('SANDBOX_MAX_RUNTIME'):
    sandbox_params['max_runtime'] = int(max_runtime)
    
if memory_limit := os.getenv('SANDBOX_MEMORY_LIMIT'):
    sandbox_params['memory_limit'] = int(memory_limit)
    
if cpu_limit := os.getenv('SANDBOX_CPU_LIMIT'):
    sandbox_params['cpu_limit'] = float(cpu_limit)

sandbox = daytona.create(**sandbox_params)

# Run the code securely inside the Sandbox
if os.getenv('DEBUG', '').lower() == 'true':
    print(f"DEBUG: Created sandbox with params: {sandbox_params}")
    
response = sandbox.process.code_run('print("Hello World from Daytona Sandbox!")')
if response.exit_code != 0:
    print(f"Error: {response.exit_code} {response.result}")
else:
    print(f"Success: {response.result}")
    
# Clean up
sandbox.cleanup()
