import pandas as pd
import matplotlib.pyplot as plt

pd = pd.read_csv('MAC_results.csv')

# Plot channel utilization against p-value
gen_periods = pd['gen_period'].unique()
result_n_p_gp = pd[['n', 'p', 'gen_period', 'successful', 'total']]
result_n_p_gp['u'] = result_n_p_gp['successful'] / result_n_p_gp['total']

for gp in gen_periods:
    ax = plt.gca()

    result_n_p = result_n_p_gp[result_n_p_gp['gen_period'] == gp]
    result_n_p = result_n_p[['n', 'p', 'u']]

    ps = result_n_p['p'].unique()

    for p in ps:
        result_n_p[result_n_p['p'] == p].plot(x='n', y='u', label=p, ax=ax)
        plt.title(f'Channel utilization against n + p for gen_period = {gp}')

    plt.xlabel('N')
    plt.ylabel("% successful packets")
    plt.savefig(f'MAC_u_n_p_gp_{gp}')
    plt.close()

N = 30
GP = 25

# Plot successful packets per node
result_n_20_gp_10_p = pd[((pd['n'] == N)) & (pd['gen_period'] == GP)]

for i in range(N):
    result_n_20_gp_10_p[f'u_{i}'] = result_n_20_gp_10_p[f'successful_{i}'] / result_n_20_gp_10_p[f'total_{i}']

result_n_20_gp_10_p = result_n_20_gp_10_p[['p'] + [f'u_{i}' for i in range(N)]]

result_n_20_gp_10_p.plot(x='p', kind='bar', legend=False)

plt.title(f'Channel utilization of nodes aginst p values, N = {N}, gp = {GP}')
plt.xlabel('p value')
plt.ylabel("% successful packets")
plt.savefig(f'MAC_nodes_u_n_{N}_gp_{GP}')