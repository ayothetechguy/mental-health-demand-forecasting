import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Scottish Health Boards
HEALTH_BOARDS = [
    'NHS Ayrshire and Arran',
    'NHS Borders',
    'NHS Dumfries and Galloway',
    'NHS Fife',
    'NHS Forth Valley',
    'NHS Grampian',
    'NHS Greater Glasgow and Clyde',
    'NHS Highland',
    'NHS Lanarkshire',
    'NHS Lothian',
    'NHS Orkney',
    'NHS Shetland',
    'NHS Tayside',
    'NHS Western Isles'
]

# Age groups
AGE_GROUPS = ['0-17', '18-25', '26-35', '36-45', '46-55', '56-65', '66-75', '76+']

# Deprivation quintiles (SIMD)
SIMD_QUINTILES = [1, 2, 3, 4, 5]

# Presentation types
PRESENTATION_TYPES = [
    'Self Harm',
    'Suicidal Ideation',
    'Acute Anxiety',
    'Depression',
    'Psychosis',
    'Substance Abuse',
    'Eating Disorder',
    'Other'
]

def generate_time_series_data(start_date, end_date, health_board):
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    data = []
    
    board_multipliers = {
        'NHS Greater Glasgow and Clyde': 2.5,
        'NHS Lothian': 2.0,
        'NHS Lanarkshire': 1.5,
        'NHS Grampian': 1.3,
        'NHS Tayside': 1.2,
        'NHS Fife': 1.0,
        'NHS Ayrshire and Arran': 1.0,
        'NHS Highland': 0.9,
        'NHS Forth Valley': 0.8,
        'NHS Dumfries and Galloway': 0.6,
        'NHS Borders': 0.4,
        'NHS Western Isles': 0.2,
        'NHS Orkney': 0.15,
        'NHS Shetland': 0.15
    }
    
    base_demand = 50 * board_multipliers.get(health_board, 1.0)
    
    for date in dates:
        day_of_week = date.dayofweek
        month = date.month
        year = date.year
        
        seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * (month - 1) / 12 + np.pi)
        day_factor = {0: 1.3, 1: 1.1, 2: 1.0, 3: 1.0, 4: 1.1, 5: 0.9, 6: 0.85}[day_of_week]
        
        covid_factor = 1.0
        if 2020 <= year <= 2021:
            covid_factor = 1.4
        elif year == 2022:
            covid_factor = 1.2
        
        year_trend = 1.0 + 0.05 * (year - 2019)
        expected_presentations = base_demand * seasonal_factor * day_factor * covid_factor * year_trend
        presentations = max(0, int(np.random.poisson(expected_presentations)))
        
        age_weights = [0.08, 0.25, 0.20, 0.15, 0.15, 0.10, 0.05, 0.02]
        age_distributions = np.random.multinomial(presentations, age_weights)
        
        for age_idx, age_group in enumerate(AGE_GROUPS):
            age_presentations = age_distributions[age_idx]
            
            if age_presentations > 0:
                simd_weights = [0.35, 0.25, 0.20, 0.12, 0.08]
                simd_distributions = np.random.multinomial(age_presentations, simd_weights)
                
                for simd_idx, simd in enumerate(SIMD_QUINTILES):
                    simd_presentations = simd_distributions[simd_idx]
                    
                    if simd_presentations > 0:
                        type_weights = [0.18, 0.22, 0.15, 0.20, 0.08, 0.10, 0.03, 0.04]
                        type_distributions = np.random.multinomial(simd_presentations, type_weights)
                        
                        for type_idx, pres_type in enumerate(PRESENTATION_TYPES):
                            count = type_distributions[type_idx]
                            
                            if count > 0:
                                data.append({
                                    'date': date,
                                    'health_board': health_board,
                                    'age_group': age_group,
                                    'simd_quintile': simd,
                                    'presentation_type': pres_type,
                                    'presentations': count
                                })
    
    return pd.DataFrame(data)

def generate_complete_dataset():
    print("Generating Mental Health Service Demand Data...")
    print("=" * 70)
    
    start_date = '2019-01-01'
    end_date = '2024-10-31'
    
    all_data = []
    
    for idx, board in enumerate(HEALTH_BOARDS, 1):
        print(f"Generating data for {board} ({idx}/{len(HEALTH_BOARDS)})...")
        board_data = generate_time_series_data(start_date, end_date, board)
        all_data.append(board_data)
    
    df = pd.concat(all_data, ignore_index=True)
    df = df.sort_values('date').reset_index(drop=True)
    
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day_of_week'] = df['date'].dt.dayofweek
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    print("\nData generation complete!")
    print(f"\nDataset Statistics:")
    print(f"  Total records: {len(df):,}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Total presentations: {df['presentations'].sum():,}")
    print(f"  Health boards: {df['health_board'].nunique()}")
    print(f"  Average daily presentations: {df.groupby('date')['presentations'].sum().mean():.1f}")
    
    return df

def save_data(df):
    df.to_csv('data/mental_health_presentations_full.csv', index=False)
    print(f"\nSaved: data/mental_health_presentations_full.csv")
    
    daily_summary = df.groupby(['date', 'health_board']).agg({
        'presentations': 'sum'
    }).reset_index()
    
    daily_summary.to_csv('data/mental_health_daily_summary.csv', index=False)
    print(f"Saved: data/mental_health_daily_summary.csv")
    
    monthly_summary = df.groupby([
        df['date'].dt.to_period('M').astype(str),
        'health_board',
        'age_group',
        'simd_quintile'
    ]).agg({
        'presentations': 'sum'
    }).reset_index()
    monthly_summary.rename(columns={'date': 'month'}, inplace=True)
    
    monthly_summary.to_csv('data/mental_health_monthly_summary.csv', index=False)
    print(f"Saved: data/mental_health_monthly_summary.csv")

if __name__ == "__main__":
    df = generate_complete_dataset()
    save_data(df)
    
    print("\n" + "=" * 70)
    print("Mental Health Data Generation Complete!")
    print("=" * 70)
