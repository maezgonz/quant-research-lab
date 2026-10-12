import numpy as np
import pandas as pd
import yfinance as yf


def define_market_states(returns, bull_threshold=0.02, bear_threshold=-0.02, window=20):
    rolling_return = returns.rolling(window).sum()
    states = np.where(rolling_return > bull_threshold, 0,
                      np.where(rolling_return < bear_threshold, 1, 2))
    return pd.Series(states, index=returns.index)


def estimate_transition_matrix(states, n_states=3):
    transition_counts = np.zeros((n_states, n_states))
    state_values = states.dropna().values

    for i in range(len(state_values) - 1):
        current_state = int(state_values[i])
        next_state = int(state_values[i + 1])
        if not np.isnan(current_state) and not np.isnan(next_state):
            transition_counts[current_state][next_state] += 1

    transition_matrix = np.zeros((n_states, n_states))
    for i in range(n_states):
        row_sum = transition_counts[i].sum()
        if row_sum > 0:
            transition_matrix[i] = transition_counts[i] / row_sum

    return transition_matrix


ticker = yf.Ticker("GGAL.BA")
df = ticker.history(period="10y", interval="1d")
returns = df['Close'].pct_change().dropna()

states = define_market_states(returns)
P = estimate_transition_matrix(states)

state_names = ['Bull', 'Bear', 'Sideways']
print("Transition Matrix:")
print(pd.DataFrame(P, index=state_names, columns=state_names).round(3))