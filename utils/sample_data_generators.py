"""
Sample data generators for different domains
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def generate_cricket_data(n_players: int = 11, n_matches: int = 10) -> pd.DataFrame:
    """
    Generate realistic cricket statistics dataset
    
    Args:
        n_players: Number of players to generate stats for
        n_matches: Number of matches to generate
        
    Returns:
        DataFrame with cricket statistics
    """
    np.random.seed(42)
    
    # Player names (mix of batting and bowling specialists)
    player_names = [
        'V. Kohli', 'R. Sharma', 'S. Tendulkar', 'M. Dhoni', 'K. Williamson',
        'J. Root', 'S. Smith', 'B. McCullum', 'A. de Villiers', 'C. Gayle',
        'J. Anderson', 'S. Afridi', 'R. Ashwin', 'M. Starc', 'B. Lee'
    ][:n_players]
    
    # Player types
    player_types = ['Batsman', 'All-Rounder', 'Bowler']
    
    data = []
    
    for match in range(1, n_matches + 1):
        for player in player_names:
            # Determine player type based on name position (rough heuristic)
            idx = player_names.index(player)
            if idx < 7:
                ptype = 'Batsman'
                batting_skill = 0.8
                bowling_skill = 0.3
            elif idx < 10:
                ptype = 'All-Rounder'
                batting_skill = 0.6
                bowling_skill = 0.6
            else:
                ptype = 'Bowler'
                batting_skill = 0.3
                bowling_skill = 0.8
            
            # Generate batting stats
            runs_scored = int(np.random.exponential(30 * batting_skill))
            runs_scored = min(runs_scored, 200)  # Cap at 200
            
            balls_faced = int(runs_scored / np.random.uniform(0.5, 1.5)) if runs_scored > 0 else 0
            balls_faced = max(balls_faced, runs_scored // 6)  # Minimum balls
            
            strike_rate = (runs_scored / balls_faced * 100) if balls_faced > 0 else 0
            
            # Boundaries (4s and 6s)
            total_boundary_runs = int(runs_scored * np.random.uniform(0.4, 0.7))
            sixes = int(total_boundary_runs / 6 * np.random.uniform(0.3, 0.5))
            fours = (total_boundary_runs - sixes * 6) // 4
            
            # Generate bowling stats
            overs_bowled = np.random.uniform(0, 10 * bowling_skill) if ptype != 'Batsman' else 0
            overs_bowled = round(overs_bowled * 2) / 2  # Round to nearest 0.5
            
            if overs_bowled > 0:
                runs_conceded = int(overs_bowled * np.random.uniform(4, 8))
                wickets_taken = np.random.poisson(overs_bowled / 5 * bowling_skill)
                wickets_taken = min(wickets_taken, 5)
                economy_rate = runs_conceded / overs_bowled if overs_bowled > 0 else 0
            else:
                runs_conceded = 0
                wickets_taken = 0
                economy_rate = 0
            
            data.append({
                'Match_ID': match,
                'Player_Name': player,
                'Player_Type': ptype,
                'Runs_Scored': runs_scored,
                'Balls_Faced': balls_faced,
                'Strike_Rate': round(strike_rate, 2),
                'Fours': fours,
                'Sixes': sixes,
                'Overs_Bowled': overs_bowled,
                'Runs_Conceded': runs_conceded,
                'Wickets_Taken': wickets_taken,
                'Economy_Rate': round(economy_rate, 2)
            })
    
    return pd.DataFrame(data)


def generate_sales_data(n_rows: int = 100) -> pd.DataFrame:
    """
    Generate realistic sales dataset
    
    Args:
        n_rows: Number of sales records to generate
        
    Returns:
        DataFrame with sales data
    """
    np.random.seed(42)
    
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=n_rows, freq='D'),
        'Product': np.random.choice(['Product A', 'Product B', 'Product C', 'Product D'], n_rows),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], n_rows),
        'Sales': np.random.uniform(1000, 10000, n_rows).round(2),
        'Units': np.random.randint(10, 200, n_rows),
        'Customer_Rating': np.random.uniform(3.0, 5.0, n_rows).round(1)
    })
    
    # Calculate price
    df['Price'] = (df['Sales'] / df['Units']).round(2)
    
    return df


def generate_finance_data(n_transactions: int = 200) -> pd.DataFrame:
    """
    Generate realistic financial transaction dataset
    
    Args:
        n_transactions: Number of transactions to generate
        
    Returns:
        DataFrame with financial transactions
    """
    np.random.seed(42)
    
    # Transaction types and categories
    categories = [
        'Salary', 'Rent', 'Groceries', 'Utilities', 'Entertainment',
        'Transportation', 'Healthcare', 'Shopping', 'Investment', 'Dining'
    ]
    
    transaction_types = []
    amounts = []
    
    for _ in range(n_transactions):
        category = np.random.choice(categories)
        
        # Different amount ranges for different categories
        if category == 'Salary':
            amount = np.random.uniform(3000, 8000)
            ttype = 'Credit'
        elif category in ['Rent', 'Investment']:
            amount = np.random.uniform(800, 2000)
            ttype = 'Debit'
        elif category in ['Groceries', 'Shopping']:
            amount = np.random.uniform(50, 500)
            ttype = 'Debit'
        elif category in ['Utilities', 'Transportation', 'Healthcare']:
            amount = np.random.uniform(30, 300)
            ttype = 'Debit'
        else:  # Entertainment, Dining
            amount = np.random.uniform(20, 200)
            ttype = 'Debit'
        
        amounts.append(round(amount, 2))
        transaction_types.append(ttype)
    
    # Account types
    account_types = ['Checking', 'Savings', 'Credit Card']
    
    df = pd.DataFrame({
        'Transaction_Date': pd.date_range('2024-01-01', periods=n_transactions, freq='D'),
        'Transaction_ID': [f'TXN{str(i+1).zfill(6)}' for i in range(n_transactions)],
        'Category': np.random.choice(categories, n_transactions),
        'Type': transaction_types,
        'Amount': amounts,
        'Account_Type': np.random.choice(account_types, n_transactions),
        'Description': [f'{cat} payment' for cat in np.random.choice(categories, n_transactions)],
        'Balance_After': 0  # Will calculate below
    })
    
    # Calculate running balance
    initial_balance = 5000
    balance = initial_balance
    balances = []
    
    for _, row in df.iterrows():
        if row['Type'] == 'Credit':
            balance += row['Amount']
        else:
            balance -= row['Amount']
        balances.append(round(balance, 2))
    
    df['Balance_After'] = balances
    
    return df


def get_sample_data(domain: str, **kwargs) -> Dict[str, Any]:
    """
    Get sample data for a specific domain
    
    Args:
        domain: One of 'cricket', 'sales', 'finance'
        **kwargs: Additional parameters for specific generators
        
    Returns:
        Dictionary with success status and dataframe
    """
    try:
        if domain.lower() == 'cricket':
            df = generate_cricket_data(**kwargs)
            description = f"Cricket statistics dataset with {len(df)} player-match records"
        elif domain.lower() == 'sales':
            df = generate_sales_data(**kwargs)
            description = f"Sales dataset with {len(df)} transactions"
        elif domain.lower() == 'finance':
            df = generate_finance_data(**kwargs)
            description = f"Financial transactions dataset with {len(df)} records"
        else:
            return {
                'success': False,
                'error': f"Unknown domain: {domain}. Choose from 'cricket', 'sales', 'finance'"
            }
        
        return {
            'success': True,
            'data': df,
            'description': description,
            'domain': domain,
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist()
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
