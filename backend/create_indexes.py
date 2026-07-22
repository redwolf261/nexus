import os
from sqlalchemy import create_engine, text

POSTGRES_USER = os.getenv('POSTGRES_USER', 'nexus_app')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'nexus_password')
POSTGRES_SERVER = os.getenv('POSTGRES_SERVER', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'nexus_db')

url = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}'
engine = create_engine(url)

with engine.connect() as conn:
    conn.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm;'))
    
    # Create GIN indexes for ILIKE and trigram search
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_person_name_trgm ON persons USING gin (name_en gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_person_phone_trgm ON persons USING gin (phone_primary gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_fir_desc_trgm ON firs USING gin (description_en gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_fir_num_trgm ON firs USING gin (fir_number gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_fir_crime_type_trgm ON firs USING gin (crime_type gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_vehicle_plate_trgm ON vehicles USING gin (license_plate gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_vehicle_make_trgm ON vehicles USING gin (make gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_vehicle_model_trgm ON vehicles USING gin (model gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_criminal_name_trgm ON criminals USING gin (name_en gin_trgm_ops);',
        'CREATE INDEX IF NOT EXISTS idx_criminal_alias_trgm ON criminals USING gin (alias_names gin_trgm_ops);',
    ]
    for idx in indexes:
        conn.execute(text(idx))
    
    # tsvector for FIR description
    conn.execute(text('ALTER TABLE firs ADD COLUMN IF NOT EXISTS search_vector tsvector;'))
    conn.execute(text("UPDATE firs SET search_vector = to_tsvector('english', coalesce(description_en, ''));"))
    conn.execute(text('CREATE INDEX IF NOT EXISTS idx_fir_search_vector ON firs USING gin(search_vector);'))
    
    conn.commit()

print('Indexes created successfully.')
