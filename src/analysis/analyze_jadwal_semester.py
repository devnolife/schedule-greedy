import pandas as pd
import sys
sys.path.append('.')
from parse_jadwal_semester import parse_jadwal_semester

def analyze_jadwal_semester():
    """Analyze JADWAL SEMESTER.xlsx untuk melihat struktur dosen yang benar"""

    # Parse JADWAL SEMESTER.xlsx
    df_clean, all_lecturers = parse_jadwal_semester()

    print('=== ANALISIS JADWAL SEMESTER.xlsx ===')
    print(f'Total courses: {len(df_clean)}')

    # Show sample data with both lecturers
    print('\nSample courses with Dosen 1 dan Dosen 2:')
    sample_with_both = df_clean[(df_clean['Dosen1'].notna()) & (df_clean['Dosen2'].notna())].head(10)

    for _, row in sample_with_both.iterrows():
        smt = row['SMT'] if pd.notna(row['SMT']) else ''
        mk = row['Mata_Kuliah'] if pd.notna(row['Mata_Kuliah']) else ''
        d1 = row['Dosen1'] if pd.notna(row['Dosen1']) else ''
        d2 = row['Dosen2'] if pd.notna(row['Dosen2']) else ''

        if str(d1).strip() and str(d2).strip():
            print(f'  {smt} - {mk}')
            print(f'    D1: {d1}')
            print(f'    D2: {d2}')
            print()

    # Count distribution of lecturer assignments
    total_courses = len(df_clean)
    with_d1 = len(df_clean[df_clean['Dosen1'].notna() & (df_clean['Dosen1'] != '')])
    with_d2 = len(df_clean[df_clean['Dosen2'].notna() & (df_clean['Dosen2'] != '')])

    # Filter for valid entries
    valid_d1 = df_clean['Dosen1'].notna() & (df_clean['Dosen1'] != '') & (df_clean['Dosen1'].astype(str).str.len() > 3)
    valid_d2 = df_clean['Dosen2'].notna() & (df_clean['Dosen2'] != '') & (df_clean['Dosen2'].astype(str).str.len() > 3)

    with_valid_d1 = len(df_clean[valid_d1])
    with_valid_d2 = len(df_clean[valid_d2])
    with_both_valid = len(df_clean[valid_d1 & valid_d2])

    print(f'\nDistribusi dosen:')
    print(f'Total courses: {total_courses}')
    print(f'Courses with valid Dosen 1: {with_valid_d1}')
    print(f'Courses with valid Dosen 2: {with_valid_d2}')
    print(f'Courses with both valid: {with_both_valid}')

    # Show unique combinations
    print('\nUnique Dosen 1 dan Dosen 2 combinations (sample):')
    valid_combinations = df_clean[valid_d1 & valid_d2][['SMT', 'Mata_Kuliah', 'Dosen1', 'Dosen2']].drop_duplicates()

    for _, row in valid_combinations.head(15).iterrows():
        print(f'  {row["SMT"]} - {row["Mata_Kuliah"]} -> D1: {row["Dosen1"]} | D2: {row["Dosen2"]}')

    # Create mapping by mata kuliah
    print('\n=== MAPPING BY MATA KULIAH ===')
    mk_lecturer_map = {}

    for _, row in df_clean.iterrows():
        if pd.notna(row['Mata_Kuliah']) and str(row['Mata_Kuliah']).strip():
            mk = str(row['Mata_Kuliah']).strip().upper()
            d1 = str(row['Dosen1']).strip() if pd.notna(row['Dosen1']) else ''
            d2 = str(row['Dosen2']).strip() if pd.notna(row['Dosen2']) else ''

            # Only include if both lecturers are valid
            if len(d1) > 3 and len(d2) > 3:
                if mk not in mk_lecturer_map:
                    mk_lecturer_map[mk] = {'D1': d1, 'D2': d2}

    print(f'Found {len(mk_lecturer_map)} mata kuliah with complete lecturer assignment')

    count = 0
    for mk, lecturers in mk_lecturer_map.items():
        print(f'  {mk} -> D1: {lecturers["D1"]} | D2: {lecturers["D2"]}')
        count += 1
        if count >= 10:
            break

    return mk_lecturer_map, df_clean

if __name__ == "__main__":
    analyze_jadwal_semester()