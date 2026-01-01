import pandas as pd
import numpy as np

def parse_jadwal_semester():
    """Parse JADWAL SEMESTER.xlsx to extract lecturer information using correct columns"""

    # Read JADWAL SEMESTER.xlsx without any skipping to get proper structure
    df_raw = pd.read_excel('/workspaces/jadwal/JADWAL SEMESTER.xlsx', sheet_name=0, header=None)

    print('Parsing JADWAL SEMESTER.xlsx with correct column structure...')
    print(f'Raw DataFrame shape: {df_raw.shape}')

    # Process each row to extract course and lecturer information
    course_data = []

    for i in range(len(df_raw)):
        row = df_raw.iloc[i]

        # Extract course information from correct columns
        smt = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ''
        mata_kuliah = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else ''

        # Extract lecturer information from columns 7 and 8 (the correct ones)
        dosen1 = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else ''
        dosen2 = str(row.iloc[8]).strip() if len(row) > 8 and pd.notna(row.iloc[8]) else ''

        # Check if this is a valid course row (has mata kuliah and at least one lecturer)
        lecturer_patterns = ['S.Kom', 'ST.,', 'MT.', 'Dr.', 'M.T', 'S.Pd']

        is_dosen1_valid = any(pattern in dosen1 for pattern in lecturer_patterns) and len(dosen1) > 10
        is_dosen2_valid = any(pattern in dosen2 for pattern in lecturer_patterns) and len(dosen2) > 10

        if mata_kuliah and len(mata_kuliah) > 3 and (is_dosen1_valid or is_dosen2_valid):
            course_data.append({
                'SMT': smt,
                'Mata_Kuliah': mata_kuliah,
                'Dosen1': dosen1 if is_dosen1_valid else '',
                'Dosen2': dosen2 if is_dosen2_valid else '',
                'row_index': i
            })

    # Convert to DataFrame
    df_clean = pd.DataFrame(course_data)

    print(f'Found {len(df_clean)} valid course entries with lecturer information')

    # Get unique lecturers
    all_lecturers = []
    for _, row in df_clean.iterrows():
        if row['Dosen1']:
            all_lecturers.append(row['Dosen1'])
        if row['Dosen2'] and row['Dosen2'] != row['Dosen1']:
            all_lecturers.append(row['Dosen2'])

    all_lecturers = list(set(all_lecturers))

    print(f'\nFound {len(all_lecturers)} unique lecturers:')
    for i, lecturer in enumerate(sorted(all_lecturers), 1):
        print(f'  {i}. {lecturer}')

    # Show sample course data with lecturers
    print('\nSample courses with lecturer assignments:')
    for _, row in df_clean.head(10).iterrows():
        dosen1 = row['Dosen1'] if row['Dosen1'] else '(kosong)'
        dosen2 = row['Dosen2'] if row['Dosen2'] else '(kosong)'
        print(f'  {row["SMT"]} - {row["Mata_Kuliah"]} | D1: {dosen1} | D2: {dosen2}')

    # Show statistics
    courses_with_both = len(df_clean[(df_clean['Dosen1'] != '') & (df_clean['Dosen2'] != '')])
    courses_with_different = len(df_clean[(df_clean['Dosen1'] != '') & (df_clean['Dosen2'] != '') & (df_clean['Dosen1'] != df_clean['Dosen2'])])

    print(f'\nStatistics:')
    print(f'Courses with both D1 and D2: {courses_with_both}')
    print(f'Courses with different D1 and D2: {courses_with_different}')

    return df_clean, all_lecturers

if __name__ == "__main__":
    parse_jadwal_semester()