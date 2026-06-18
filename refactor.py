import os
import shutil
import re

# Base directory
BASE_DIR = r"c:\Users\Oryza\SEM4\BigData-infocheck-id"
os.chdir(BASE_DIR)

# Folders to create
folders = ['api', 'producers', 'consumers', 'ml', 'utils', 'scripts']
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Files to move
files_to_move = {
    'predict_api.py': 'api',
    'komdigi_similarity.py': 'api',
    'scraper_kominfo.py': 'producers',
    'rss_producer.py': 'producers',
    'telegram_producer.py': 'producers',
    'stream_consumer.py': 'consumers',
    'kafka_helper.py': 'utils',
    'nlp_baseline.py': 'ml',
    'active_learning.py': 'ml',
    'prepare_dataset.py': 'scripts',
    'test_gemini.py': 'scripts'
}

for file_name, dest_folder in files_to_move.items():
    if os.path.exists(file_name):
        shutil.move(file_name, os.path.join(dest_folder, file_name))

def add_sys_path(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # If already added, skip
    if 'sys.path.append' in content: return

    # find first import line
    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_idx = i
            break
            
    sys_path_code = "import sys, os\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
    lines.insert(insert_idx, sys_path_code)
    
    # fix kafka import
    content = '\n'.join(lines)
    content = re.sub(r'from kafka_helper import', r'from utils.kafka_helper import', content)
    content = re.sub(r'import kafka_helper', r'import utils.kafka_helper as kafka_helper', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Fix producers
add_sys_path('producers/rss_producer.py')
add_sys_path('producers/telegram_producer.py')
add_sys_path('producers/scraper_kominfo.py')
add_sys_path('consumers/stream_consumer.py')

# Fix predict_api.py
api_file = 'api/predict_api.py'
if os.path.exists(api_file):
    with open(api_file, 'r', encoding='utf-8') as f:
        api_content = f.read()
    api_content = re.sub(r'from komdigi_similarity import', r'from .komdigi_similarity import', api_content)
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(api_content)

# Fix Dockerfile
docker_file = 'Dockerfile'
if os.path.exists(docker_file):
    with open(docker_file, 'r', encoding='utf-8') as f:
        docker_content = f.read()
    docker_content = re.sub(r'COPY komdigi_similarity.py \.', r'COPY api/komdigi_similarity.py api/', docker_content)
    docker_content = re.sub(r'COPY predict_api.py \.', r'COPY api/predict_api.py api/', docker_content)
    docker_content = re.sub(r'CMD \["uvicorn", "predict_api:app"', r'CMD ["uvicorn", "api.predict_api:app"', docker_content)
    with open(docker_file, 'w', encoding='utf-8') as f:
        f.write(docker_content)
        
print("Refactoring done.")
