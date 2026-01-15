
import sys
import os

# Add script directory to path explicitly
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

print(f"Testing module imports from: {script_dir}")

try:
    print("Importing config...")
    from modules import config
    print(f"  Loaded config from: {config.__file__}")
    
    print("Importing result_types...")
    from modules import result_types
    
    print("Importing request_metadata...")
    from modules import request_metadata
    
    print("Importing utils...")
    from modules.utils import pdf_utils, zip_utils, report_builder
    
    print("Importing schemas...")
    from modules.schemas import invoice, obl, hawb, packing_list
    
    print("Importing transformation...")
    from modules.transformation import data_processor
    
    print("Importing validator components...")
    from modules.validators import errors, data_validator, validation_engine
    
    # input_validator imports pypdf which should be there
    from modules.validators import input_validator

    print("Importing document_splitter...")
    from modules.document_splitter import splitter

    print("ALL MODULES IMPORTED SUCCESSFULLY!")
    
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
